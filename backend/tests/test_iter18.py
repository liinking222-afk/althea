"""
Iteration 18 tests: Neural Interface (ANIP/1.0), Live Web Uplink,
In-Band Autosynth, plus light regression on core Althea endpoints.
"""
import os
import struct
import base64
import math
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback for direct pytest run
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- Neural protocol ----------
def test_neural_protocol(s):
    r = s.get(f"{API}/neural/protocol", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("protocol", "").startswith("ANIP/1.0") or d.get("name", "").startswith("ANIP")
    # Best-effort field checks
    assert "formats" in d or "supported_formats" in d
    assert "bands_hz" in d or "bands" in d
    assert "substrate" in d or "substrates" in d or "engines" in d


# ---------- Synthetic decode across all 5 states ----------
@pytest.mark.parametrize(
    "state,expected_substr",
    [
        ("focus", "FOCUSED"),
        ("rest", "RELAXED"),
        ("drowsy", "DROWSY"),
        ("motor-left", "LEFT"),
        ("motor-right", "RIGHT"),
    ],
)
def test_neural_synthetic_states(s, state, expected_substr):
    r = s.post(
        f"{API}/neural/synthetic",
        json={"state": state, "decode": True, "seed": 42},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    decoded = (d.get("decode") or {}).get("decoded_state", "") or d.get("decoded_state", "")
    assert expected_substr in decoded.upper(), f"state={state} decoded={decoded}"
    ver = (d.get("decode") or {}).get("verification") or d.get("verification") or {}
    assert ver.get("all_passed") is True, ver


# ---------- Custom-channel decode ----------
def test_neural_decode_custom_sine(s):
    fs = 128
    n = 512
    t = [i / fs for i in range(n)]
    sig = [math.sin(2 * math.pi * 10 * ti) for ti in t]
    payload = {"channels": [{"label": "C3", "samples": sig},
                             {"label": "C4", "samples": sig}], "fs": fs}
    r = s.post(f"{API}/neural/decode", json=payload, timeout=60)
    assert r.status_code == 200, r.text
    d = r.json()
    # Alpha (8-12 Hz) should dominate for 10Hz sine — spec says alpha-dominant
    decoded = d.get("decoded_state", "")
    assert "ALPHA" in decoded.upper() or "RELAX" in decoded.upper(), decoded
    assert d.get("verification", {}).get("all_passed") is True
    assert "band_powers" in d or "bands" in d or "channels" in d
    assert "spikes" in d or any("spikes" in ch for ch in d.get("channels", []))
    # fusion attention rows sum ~1
    fusion = d.get("fusion") or d.get("attention") or {}
    attn = fusion.get("attention") if isinstance(fusion, dict) else None
    if attn:
        for row in attn:
            assert abs(sum(row) - 1.0) < 1e-3, row


def test_neural_decode_channel_too_short(s):
    r = s.post(f"{API}/neural/decode",
               json={"channels": [{"label": "c1", "samples": [0.0] * 8}], "fs": 128},
               timeout=15)
    assert r.status_code == 400, r.text
    assert "channel_too_short" in r.text.lower() or "too_short" in r.text.lower()


# ---------- EDF parse ----------
def _build_edf(fs=128, seconds=2, n_signals=1) -> bytes:
    """Minimal spec-valid EDF with n_signals channels of int16 LE data."""
    n_samples = fs * seconds
    header_bytes = 256 + 256 * n_signals

    # Main header (256 bytes)
    version = "0".ljust(8)
    patient = "X X X X".ljust(80)
    recording = "Startdate X X X X".ljust(80)
    startdate = "01.01.26"
    starttime = "00.00.00"
    header_len = str(header_bytes).ljust(8)
    reserved = " ".ljust(44)
    num_records = str(seconds).ljust(8)  # 1 record per second
    dur_record = "1       "  # 1 sec
    ns = str(n_signals).ljust(4)

    main = (version + patient + recording + startdate + starttime +
            header_len + reserved + num_records + dur_record + ns).encode("ascii")
    assert len(main) == 256, len(main)

    # Signal header (256 bytes per signal)
    labels = ("EEG C3".ljust(16) * n_signals).encode("ascii")
    transducer = ("AgAgCl".ljust(80) * n_signals).encode("ascii")
    phys_dim = ("uV".ljust(8) * n_signals).encode("ascii")
    phys_min = ("-100".ljust(8) * n_signals).encode("ascii")
    phys_max = ("100".ljust(8) * n_signals).encode("ascii")
    dig_min = ("-32768".ljust(8) * n_signals).encode("ascii")
    dig_max = ("32767".ljust(8) * n_signals).encode("ascii")
    prefilt = ("HP:0.1Hz LP:75Hz".ljust(80) * n_signals).encode("ascii")
    samples_per_rec = (str(fs).ljust(8) * n_signals).encode("ascii")
    reserved_sig = (" " * 32 * n_signals).encode("ascii")

    sig_header = (labels + transducer + phys_dim + phys_min + phys_max +
                  dig_min + dig_max + prefilt + samples_per_rec + reserved_sig)
    assert len(sig_header) == 256 * n_signals

    # Data: seconds records, each record has fs samples per signal, int16 LE
    data = bytearray()
    for _ in range(seconds):
        for _ in range(n_signals):
            for i in range(fs):
                val = int(1000 * math.sin(2 * math.pi * 10 * i / fs))
                data += struct.pack("<h", val)
    return main + sig_header + bytes(data)


def test_edf_parse_valid(s):
    edf = _build_edf()
    b64 = base64.b64encode(edf).decode()
    r = s.post(f"{API}/neural/edf/parse", json={"b64": b64, "decode": True}, timeout=60)
    assert r.status_code == 200, r.text[:500]
    d = r.json()
    assert d.get("format", "").upper().startswith("EDF") or "edf" in str(d).lower()
    assert d.get("fs") in (128, 128.0) or (d.get("parsed") or {}).get("fs") in (128, 128.0)


def test_edf_parse_invalid_base64(s):
    r = s.post(f"{API}/neural/edf/parse", json={"b64": "!!!not-base64!!!"}, timeout=15)
    assert r.status_code in (400, 422), r.text


def test_edf_parse_garbage(s):
    b64 = base64.b64encode(b"this is not an EDF file at all, just random bytes ~~~").decode()
    r = s.post(f"{API}/neural/edf/parse", json={"b64": b64}, timeout=15)
    assert r.status_code == 422, r.text


# ---------- Substrate engines ----------
def test_substrate_lattice_energy(s):
    r = s.post(f"{API}/neural/substrate/lattice-energy",
               json={"n": 32, "steps": 64, "seed": 3}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    traj = d.get("energy_trajectory") or d.get("trajectory") or []
    assert len(traj) >= 2
    for a, b in zip(traj, traj[1:]):
        assert b <= a + 1e-6, f"energy increased {a}->{b}"
    assert d.get("verification", {}).get("all_passed") is True


def test_substrate_propagate(s):
    r = s.post(f"{API}/neural/substrate/propagate",
               json={"n_neurons": 16, "duration_ms": 300, "seed": 5}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("total_spikes", 0) > 0
    assert d.get("verification", {}).get("all_passed") is True


def test_substrate_fuse(s):
    mat = [[0.1, 0.2, 0.3, 0.4, 0.5],
           [0.5, 0.4, 0.3, 0.2, 0.1],
           [0.2, 0.2, 0.2, 0.2, 0.2]]
    r = s.post(f"{API}/neural/substrate/fuse", json={"matrix": mat}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    attn = d.get("attention") or d.get("attention_weights") or []
    assert attn, d
    for row in attn:
        assert abs(sum(row) - 1.0) < 1e-3, row
    assert d.get("verification", {}).get("all_passed") is True


def test_neural_sessions(s):
    r = s.get(f"{API}/neural/sessions", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    # after decodes done above, we should have >=1
    sessions = d if isinstance(d, list) else d.get("sessions", [])
    assert isinstance(sessions, list)


# ---------- Web Uplink ----------
def test_web_status(s):
    r = s.get(f"{API}/web/status", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("online") is True or d.get("uplink", "").lower() == "online" or d.get("status", "").lower() == "online"


def test_web_search(s):
    r = s.post(f"{API}/web/search", json={"query": "python programming"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    results = d.get("results", [])
    assert len(results) > 0
    first = results[0]
    assert "title" in first and ("url" in first or "href" in first)


def test_web_fetch(s):
    r = s.post(f"{API}/web/fetch", json={"url": "https://example.com"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    text_field = (d.get("text") or d.get("content") or "") + " " + (d.get("title") or "")
    assert "Example Domain" in text_field


# ---------- In-band autosynth chat ----------
def test_chat_autosynth_plot(s):
    r = s.post(f"{API}/chat",
               json={"message": "plot these numbers: 3 7 2 9 4 8 1",
                     "session_id": "test-e2e-autosynth"},
               timeout=120)
    assert r.status_code == 200, r.text
    d = r.json()
    reply = d.get("reply") or d.get("message") or ""
    tags = d.get("tags") or []
    assert "[AUTOSYNTH-INVOKE" in reply, reply[:400]
    assert "[SYNTH-IMAGE:data:image/png" in reply, reply[:400]
    assert "AUTOSYNTH" in tags, tags


# ---------- Regression ----------
def test_reg_status(s):
    r = s.get(f"{API}/status", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "OPERATIONAL"


def test_reg_diagnostics(s):
    r = s.get(f"{API}/diagnostics", timeout=15)
    assert r.status_code == 200
    assert "verdict" in r.json()


def test_reg_workers(s):
    r = s.get(f"{API}/workers", timeout=10)
    assert r.status_code == 200
    d = r.json()
    cores = d.get("cores") or d.get("workers") or []
    assert len(cores) == 8
    assert d.get("loop_running") is True or any(c.get("loop_running") for c in cores if isinstance(c, dict))


def test_reg_synthesize(s):
    r = s.post(f"{API}/synthesize/from-dialogue", json={"force": True}, timeout=30)
    assert r.status_code == 200


def test_reg_chat_history(s):
    r = s.get(f"{API}/chat/history/test-e2e-autosynth", timeout=15)
    assert r.status_code == 200
    d = r.json()
    turns = d if isinstance(d, list) else d.get("turns") or d.get("history") or []
    assert len(turns) >= 1
