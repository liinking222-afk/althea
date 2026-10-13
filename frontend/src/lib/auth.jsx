import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;
const TOKEN_KEY = "althea_auth_token";

axios.defaults.withCredentials = true;
axios.interceptors.request.use((config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && !config.headers?.Authorization) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(undefined); // undefined = loading, null = signed out

    const refresh = useCallback(async () => {
        try {
            const res = await axios.get(`${API}/auth/me`);
            setUser(res.data);
            return res.data;
        } catch {
            localStorage.removeItem(TOKEN_KEY);
            setUser(null);
            return null;
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    useEffect(() => {
        const id = axios.interceptors.response.use(
            (r) => r,
            (err) => {
                if (err?.response?.status === 401 && !String(err.config?.url || "").includes("/auth/")) {
                    localStorage.removeItem(TOKEN_KEY);
                    setUser(null);
                }
                return Promise.reject(err);
            },
        );
        return () => axios.interceptors.response.eject(id);
    }, []);

    const accept = (data) => {
        if (data?.token) localStorage.setItem(TOKEN_KEY, data.token);
        setUser(data.user);
        return data.user;
    };

    const value = useMemo(() => ({
        user,
        refresh,
        login: async (email, password) => accept((await axios.post(`${API}/auth/login`, { email, password })).data),
        register: async (email, password, name) =>
            accept((await axios.post(`${API}/auth/register`, { email, password, name })).data),
        exchangeGoogleSession: async (session_id) =>
            accept((await axios.post(`${API}/auth/session`, { session_id })).data),
        logout: async () => {
            try { await axios.post(`${API}/auth/logout`); } catch { /* ignore */ }
            localStorage.removeItem(TOKEN_KEY);
            setUser(null);
        },
        setUser,
    }), [user, refresh]);

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
