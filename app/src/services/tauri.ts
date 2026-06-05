const LOCAL_API = "http://127.0.0.1:17421";

function isTauriEnv(): boolean {
  return "__TAURI_INTERNALS__" in window;
}

export async function startConnection(configJson: string): Promise<string> {
  if (isTauriEnv()) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<string>("start_connection", { configJson });
  }
  const res = await fetch(`${LOCAL_API}/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: configJson,
  });
  if (!res.ok) throw new Error("Не удалось запустить sing-box");
  const data = await res.json();
  return data.message;
}

export async function stopConnection(): Promise<string> {
  if (isTauriEnv()) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<string>("stop_connection");
  }
  const res = await fetch(`${LOCAL_API}/disconnect`, { method: "POST" });
  if (!res.ok) throw new Error("Не удалось остановить sing-box");
  const data = await res.json();
  return data.message;
}

export async function getConnectionStatus(): Promise<boolean> {
  if (isTauriEnv()) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<boolean>("get_connection_status");
  }
  try {
    const res = await fetch(`${LOCAL_API}/status`);
    if (!res.ok) return false;
    const data = await res.json();
    return !!data.connected;
  } catch {
    return false;
  }
}

export async function copyToClipboard(text: string): Promise<void> {
  if (isTauriEnv()) {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("copy_to_clipboard", { text });
  } else {
    await navigator.clipboard.writeText(text);
  }
}

export async function openTelegram(): Promise<void> {
  if (isTauriEnv()) {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("open_telegram");
  } else {
    window.open("https://t.me/Seb0g1", "_blank");
  }
}

export async function setMinimizeOnClose(enabled: boolean): Promise<void> {
  if (!isTauriEnv()) return;
  const { invoke } = await import("@tauri-apps/api/core");
  await invoke("set_minimize_on_close", { enabled });
}

export function setupTrayListeners(
  onConnect: () => void,
  onDisconnect: () => void
): () => void {
  if (!isTauriEnv()) return () => {};

  let unlistenConnect: (() => void) | undefined;
  let unlistenDisconnect: (() => void) | undefined;

  void (async () => {
    const { listen } = await import("@tauri-apps/api/event");
    unlistenConnect = await listen("tray-connect", onConnect);
    unlistenDisconnect = await listen("tray-disconnect", onDisconnect);
  })();

  return () => {
    unlistenConnect?.();
    unlistenDisconnect?.();
  };
}
