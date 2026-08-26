import React from "react";
import ReactDOM from "react-dom/client";
import "katex/dist/katex.min.css";
import "@/index.css";
import App from "@/App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}

// Capture the PWA install prompt so the Device Bridge can offer a one-tap install.
window.__althea_install = null;
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  window.__althea_install = e;
  window.dispatchEvent(new Event("althea:installable"));
});
