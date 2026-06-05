import type { AppSettings, Mode } from "../types";
import { DEFAULT_SERVICES } from "./catalog";

const STORAGE_KEY = "inetfix_settings";

const defaults: AppSettings = {
  key: "",
  mode: "combined",
  selectedServices: [...DEFAULT_SERVICES],
  autostart: "none",
  minimizeOnStart: false,
  minimizeOnClose: true,
  apiUrl: import.meta.env.VITE_API_URL || "http://localhost:8080",
};

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...defaults };
    return { ...defaults, ...JSON.parse(raw) };
  } catch {
    return { ...defaults };
  }
}

export function saveSettings(settings: AppSettings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export function updateSettings(partial: Partial<AppSettings>): AppSettings {
  const current = loadSettings();
  const next = { ...current, ...partial };
  saveSettings(next);
  return next;
}

export function setMode(mode: Mode): AppSettings {
  return updateSettings({ mode });
}
