import { useCallback, useEffect, useState } from "react";
import { TitleBar } from "./components/TitleBar";
import { MainScreen } from "./components/MainScreen";
import { ServicesScreen } from "./components/ServicesScreen";
import { AccountScreen } from "./components/AccountScreen";
import { ActivateScreen } from "./components/ActivateScreen";
import { fetchConfig } from "./services/api";
import { loadSettings, saveSettings, updateSettings } from "./services/storage";
import {
  getConnectionStatus,
  openTelegram,
  startConnection,
  stopConnection,
} from "./services/tauri";
import type { AppSettings, Mode, Screen } from "./types";

export default function App() {
  const [screen, setScreen] = useState<Screen>("main");
  const [settings, setSettings] = useState<AppSettings>(loadSettings);
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    if (!settings.key) {
      setScreen("activate");
    }
    getConnectionStatus().then(setConnected).catch(() => {});
  }, []);

  const handleModeChange = (mode: Mode) => {
    const next = updateSettings({ mode });
    setSettings(next);
  };

  const handleToggleService = (id: string) => {
    const current = settings.selectedServices;
    const next = current.includes(id)
      ? current.filter((s) => s !== id)
      : [...current, id];
    const updated = updateSettings({ selectedServices: next });
    setSettings(updated);
  };

  const handleToggleConnection = useCallback(async () => {
    if (!settings.key) {
      setScreen("activate");
      return;
    }

    if (connected) {
      setConnecting(true);
      try {
        await stopConnection();
        setConnected(false);
      } catch (e) {
        console.error(e);
      } finally {
        setConnecting(false);
      }
      return;
    }

    setConnecting(true);
    try {
      const data = await fetchConfig(
        settings.key,
        settings.mode,
        settings.selectedServices,
        settings.apiUrl
      );
      await startConnection(JSON.stringify(data.singbox));
      setConnected(true);
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "Ошибка подключения");
    } finally {
      setConnecting(false);
    }
  }, [connected, settings]);

  const handleActivated = (key: string) => {
    const next = updateSettings({ key });
    setSettings(next);
    setScreen("main");
  };

  const handleLogout = () => {
    stopConnection().catch(() => {});
    const next = updateSettings({ key: "" });
    setSettings(next);
    setConnected(false);
    setScreen("activate");
  };

  const handleSettingsChange = (partial: Partial<AppSettings>) => {
    setSettings((s) => ({ ...s, ...partial }));
  };

  const handleSaveSettings = () => {
    saveSettings(settings);
    setScreen("main");
  };

  return (
    <div className="app">
      <TitleBar
        onSettings={screen === "main" ? () => setScreen("account") : undefined}
        onTelegram={() => openTelegram()}
        showBack={screen !== "main" && screen !== "activate"}
        onBack={() => setScreen("main")}
      />

      {screen === "activate" && (
        <ActivateScreen apiUrl={settings.apiUrl} onActivated={handleActivated} />
      )}

      {screen === "main" && settings.key && (
        <MainScreen
          mode={settings.mode}
          connected={connected}
          connecting={connecting}
          userKey={settings.key}
          onModeChange={handleModeChange}
          onToggleConnection={handleToggleConnection}
          onSelectServices={() => setScreen("services")}
        />
      )}

      {screen === "services" && (
        <ServicesScreen
          selected={settings.selectedServices}
          onToggle={handleToggleService}
          onBack={() => setScreen("main")}
        />
      )}

      {screen === "account" && (
        <AccountScreen
          settings={settings}
          onChange={handleSettingsChange}
          onLogout={handleLogout}
          onBack={() => setScreen("main")}
          onSave={handleSaveSettings}
        />
      )}
    </div>
  );
}
