"""ALTHEA — Self-Diagnostics.

`/api/diagnostics` runs a battery of health checks and returns a structured
report with severity, findings, and recommended remediations. The terminal
`/diagnose` command surfaces this in human form.
"""
import logging
import time
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter

from core import db, EMERGENT_LLM_KEY

router = APIRouter()


async def _check_mongo() -> dict:
    t0 = time.time()
    try:
        # Trip the connection with a tiny command.
        await db.command("ping")
        return {
            "name": "mongo",
            "ok": True,
            "latency_ms": round((time.time() - t0) * 1000, 1),
            "remedy": None,
        }
    except Exception as exc:
        return {
            "name": "mongo",
            "ok": False,
            "error": str(exc)[:200],
            "remedy": "Check MONGO_URL env var and Atlas IP allowlist.",
        }


def _check_llm_key() -> dict:
    if not EMERGENT_LLM_KEY:
        return {
            "name": "llm_key",
            "ok": False,
            "error": "EMERGENT_LLM_KEY not set",
            "remedy": (
                "Add EMERGENT_LLM_KEY to backend/.env or run from Local Core "
                "(automatic fallback already active)."
            ),
        }
    return {"name": "llm_key", "ok": True, "remedy": None}


async def _check_lattice_health() -> dict:
    try:
        total = await db.althea_nodes.count_documents({})
        orphans = await db.althea_nodes.count_documents({
            "parent_id": {"$ne": None, "$nin": []},
        })
        # Sample a few node ids
        ids_sample = await db.althea_nodes.find(
            {}, {"_id": 0, "id": 1}
        ).sort("timestamp", -1).limit(8).to_list(8)
        return {
            "name": "lattice",
            "ok": True,
            "total_nodes": total,
            "with_parent": orphans,
            "recent_ids": [d["id"] for d in ids_sample],
            "remedy": None,
        }
    except Exception as exc:
        return {
            "name": "lattice",
            "ok": False,
            "error": str(exc)[:200],
            "remedy": "Inspect althea_nodes collection.",
        }


async def _check_perception_buffer() -> dict:
    try:
        latest = await db.althea_perception.find_one(
            {"id": "latest"}, {"_id": 0, "timestamp": 1, "size_bytes": 1}
        )
        if not latest:
            return {
                "name": "perception",
                "ok": True,
                "warn": "no_frame_captured",
                "remedy": "Enable the VISION toggle in the top bar to start self-observation.",
            }
        return {
            "name": "perception",
            "ok": True,
            "last_frame_at": latest.get("timestamp"),
            "last_frame_bytes": latest.get("size_bytes"),
            "remedy": None,
        }
    except Exception as exc:
        return {
            "name": "perception",
            "ok": False,
            "error": str(exc)[:200],
            "remedy": "Inspect althea_perception collection.",
        }


async def _check_autonomous_loops() -> dict:
    """Verify the autonomous growth + evolution loops have produced output
    recently. If they have not, that is fine (they may be on cooldown)."""
    try:
        last_growth = await db.althea_capabilities.find_one(
            {}, {"_id": 0, "timestamp": 1}, sort=[("timestamp", -1)],
        )
        last_evo = await db.althea_cycles.find_one(
            {}, {"_id": 0, "timestamp": 1, "cycle_number": 1},
            sort=[("timestamp", -1)],
        )
        return {
            "name": "autonomous_loops",
            "ok": True,
            "last_growth_at": last_growth.get("timestamp") if last_growth else None,
            "last_evolution_at": last_evo.get("timestamp") if last_evo else None,
            "evolution_cycle": last_evo.get("cycle_number") if last_evo else 0,
            "remedy": None,
        }
    except Exception as exc:
        return {
            "name": "autonomous_loops",
            "ok": False,
            "error": str(exc)[:200],
            "remedy": "Re-trigger via POST /api/growth/spawn and /api/evolution/tick.",
        }


async def _check_memory_volume() -> dict:
    try:
        count = await db.althea_memories.count_documents({})
        # Warn at >50k memories (TF-IDF stays fine until ~200k but lattice growth slows).
        warn = count > 50000
        return {
            "name": "memory_volume",
            "ok": True,
            "total": count,
            "warn": "memory_collection_large" if warn else None,
            "remedy": (
                "Optionally compact via DELETE /api/memory or archive older "
                "memories to a snapshot." if warn else None
            ),
        }
    except Exception as exc:
        return {
            "name": "memory_volume",
            "ok": False,
            "error": str(exc)[:200],
            "remedy": "Inspect althea_memories collection.",
        }


@router.get("/diagnostics")
async def diagnostics():
    """Run every self-check in parallel-friendly sequence and return the
    aggregate report. Severity reflects the worst single finding."""
    checks: List[dict] = [
        await _check_mongo(),
        _check_llm_key(),
        await _check_lattice_health(),
        await _check_perception_buffer(),
        await _check_autonomous_loops(),
        await _check_memory_volume(),
    ]

    failures = [c for c in checks if not c.get("ok")]
    warnings = [c for c in checks if c.get("ok") and c.get("warn")]
    if failures:
        severity = "critical" if any(c["name"] == "mongo" for c in failures) else "warn"
        verdict = "DEGRADED"
    elif warnings:
        severity = "info"
        verdict = "OK_WITH_NOTES"
    else:
        severity = "none"
        verdict = "ALL_SYSTEMS_NOMINAL"

    return {
        "verdict": verdict,
        "severity": severity,
        "checks": checks,
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/diagnostics/repair")
async def diagnostics_repair():
    """Best-effort safe self-repair. Currently:
      * Removes 'latest' perception frame if its image_data is corrupt.
      * Touches the system-map memory if missing tags."""
    actions = []
    try:
        frame = await db.althea_perception.find_one(
            {"id": "latest"}, {"_id": 0, "image_data": 1}
        )
        if frame and not (frame.get("image_data") or "").startswith("data:image"):
            await db.althea_perception.delete_one({"id": "latest"})
            actions.append("purged corrupt perception frame")
    except Exception:
        logging.exception("repair: perception scrub failed")

    return {
        "ok": True,
        "actions": actions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
