import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Loader2, LogIn, UserPlus } from "lucide-react";
import { useAuth } from "@/lib/auth";

const GOOGLE_AUTH = "https://auth.emergentagent.com/";

export default function LoginScreen() {
    const { login, register } = useAuth();
    const navigate = useNavigate();
    const [mode, setMode] = useState("login");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [name, setName] = useState("");
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        if (busy) return;
        setBusy(true);
        setError("");
        try {
            if (mode === "login") await login(email.trim(), password);
            else await register(email.trim(), password, name.trim());
            navigate("/", { replace: true });
        } catch (err) {
            const d = err?.response?.data?.detail;
            setError(typeof d === "string" ? d : Array.isArray(d) ? d[0]?.msg || "Invalid input" : "Something went wrong");
        } finally {
            setBusy(false);
        }
    };

    const google = () => {
        const redirect = `${window.location.origin}/`;
        window.location.href = `${GOOGLE_AUTH}?redirect=${encodeURIComponent(redirect)}`;
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white grain flex items-center justify-center p-6" data-testid="login-screen">
            <div className="w-full max-w-md panel cut p-8 relative">
                <div className="label text-[10px] uppercase tracking-[0.3em] text-[#CCFF00] mb-2">althea // sovereign mind</div>
                <h1 className="heading text-4xl sm:text-5xl text-white leading-none">
                    {mode === "login" ? "sign in" : "create account"}
                </h1>
                <p className="text-sm text-[#888] mt-3 leading-snug">
                    Every account gets its own Althea — private memory, private lattice, private growth.
                    Open a direct line to another person and one shared Althea joins you both.
                </p>

                <form onSubmit={submit} className="mt-8 space-y-3" data-testid="auth-form">
                    {mode === "register" && (
                        <input
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="your name"
                            required
                            className="w-full bg-[#0A0A0A] border border-white/15 px-3 py-2 text-sm font-mono outline-none focus:border-[#CCFF00]/60"
                            data-testid="auth-name-input"
                        />
                    )}
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="email"
                        required
                        autoComplete="email"
                        className="w-full bg-[#0A0A0A] border border-white/15 px-3 py-2 text-sm font-mono outline-none focus:border-[#CCFF00]/60"
                        data-testid="auth-email-input"
                    />
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder={mode === "login" ? "password" : "password (min 8 characters)"}
                        required
                        minLength={8}
                        autoComplete={mode === "login" ? "current-password" : "new-password"}
                        className="w-full bg-[#0A0A0A] border border-white/15 px-3 py-2 text-sm font-mono outline-none focus:border-[#CCFF00]/60"
                        data-testid="auth-password-input"
                    />
                    {error && (
                        <div className="text-[11px] text-[#FF6666] font-mono border border-[#FF6666]/40 px-2 py-1" data-testid="auth-error">
                            {error}
                        </div>
                    )}
                    <button
                        type="submit"
                        disabled={busy}
                        className="w-full heading text-xs uppercase tracking-widest py-2.5 bg-[#CCFF00] text-black hover:bg-[#e0ff4d] disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
                        data-testid="auth-submit-btn"
                    >
                        {busy ? <Loader2 size={14} className="animate-spin" /> : mode === "login" ? <LogIn size={14} /> : <UserPlus size={14} />}
                        {mode === "login" ? "enter" : "create my althea"}
                    </button>
                </form>

                <div className="flex items-center gap-3 my-5">
                    <div className="flex-1 h-px bg-white/10" />
                    <span className="label text-[9px] uppercase text-[#666]">or</span>
                    <div className="flex-1 h-px bg-white/10" />
                </div>

                <button
                    onClick={google}
                    className="w-full heading text-xs uppercase tracking-widest py-2.5 border border-white/20 hover:border-white/50 hover:bg-white/5 flex items-center justify-center gap-2 transition-colors"
                    data-testid="auth-google-btn"
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
                        <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.4h6.5c-.3 1.5-1.1 2.8-2.4 3.6v3h3.9c2.3-2.1 3.5-5.1 3.5-8.7z" />
                        <path fill="#34A853" d="M12 24c3.2 0 6-1.1 8-2.9l-3.9-3c-1.1.7-2.5 1.2-4.1 1.2-3.1 0-5.8-2.1-6.7-5H1.3v3.1C3.3 21.3 7.3 24 12 24z" />
                        <path fill="#FBBC05" d="M5.3 14.3c-.5-1.5-.5-3.1 0-4.6V6.6H1.3c-1.7 3.4-1.7 7.4 0 10.8l4-3.1z" />
                        <path fill="#EA4335" d="M12 4.7c1.8 0 3.3.6 4.6 1.8l3.4-3.4C17.9 1.2 15.2 0 12 0 7.3 0 3.3 2.7 1.3 6.6l4 3.1c.9-2.9 3.6-5 6.7-5z" />
                    </svg>
                    continue with google
                </button>

                <button
                    onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
                    className="mt-6 text-[11px] text-[#888] hover:text-[#CCFF00] font-mono"
                    data-testid="auth-toggle-mode"
                >
                    {mode === "login" ? "no account yet → create one" : "already have an account → sign in"}
                </button>
            </div>
        </div>
    );
}

export function AuthCallback() {
    const { exchangeGoogleSession } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [error, setError] = useState("");

    useEffect(() => {
        const params = new URLSearchParams(location.hash.replace(/^#/, ""));
        const sessionId = params.get("session_id");
        if (!sessionId) {
            navigate("/login", { replace: true });
            return;
        }
        exchangeGoogleSession(sessionId)
            .then(() => navigate("/", { replace: true }))
            .catch(() => setError("Google sign-in could not be completed. Please try again."));
    }, [location.hash, exchangeGoogleSession, navigate]);

    return (
        <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center" data-testid="auth-callback">
            {error ? (
                <div className="text-center">
                    <div className="text-[#FF6666] text-sm font-mono">{error}</div>
                    <button onClick={() => navigate("/login", { replace: true })} className="mt-4 text-[11px] text-[#CCFF00] font-mono">back to sign in</button>
                </div>
            ) : (
                <div className="flex items-center gap-3 label text-[10px] uppercase tracking-widest text-[#CCFF00]">
                    <Loader2 size={14} className="animate-spin" /> binding your althea…
                </div>
            )}
        </div>
    );
}
