import type { Mode } from "../types";

const DEFAULT_API = import.meta.env.VITE_API_URL || "http://localhost:8080";

export async function validateKey(key: string, apiUrl = DEFAULT_API) {
  const res = await fetch(`${apiUrl}/api/v1/keys/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key }),
  });
  if (!res.ok) throw new Error("Неверный или просроченный ключ");
  return res.json();
}

export async function fetchConfig(
  key: string,
  mode: Mode,
  services: string[],
  apiUrl = DEFAULT_API
) {
  const params = new URLSearchParams({
    mode,
    services: services.join(","),
  });
  const res = await fetch(
    `${apiUrl}/api/v1/config/${encodeURIComponent(key.replace(/\s/g, ""))}?${params}`
  );
  if (!res.ok) throw new Error("Не удалось получить конфигурацию");
  return res.json();
}
