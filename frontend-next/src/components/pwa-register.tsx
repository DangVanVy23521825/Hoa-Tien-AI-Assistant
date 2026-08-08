"use client";

import { useEffect } from "react";

/** Đăng ký service worker (public/sw.js) — PWA "cài app" + mở được khi mất mạng. */
export default function PwaRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }, []);

  return null;
}
