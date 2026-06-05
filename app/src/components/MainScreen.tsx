import { useEffect, useState } from "react";
import type { Mode } from "../types";

interface MainScreenProps {
  mode: Mode;
  connected: boolean;
  connecting: boolean;
  userKey: string;
  onModeChange: (mode: Mode) => void;
  onToggleConnection: () => void;
  onSelectServices: () => void;
}

const descriptions: Record<Mode, string> = {
  combined:
    "В комбинированном режиме FixInet.ez работает только для выбранных сайтов или приложений, чтобы не замедлять остальные сервисы",
  full: "В полном режиме весь интернет-трафик проходит через FixInet.ez для максимальной защиты и стабильности",
};

function formatTimer(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
}

export function MainScreen({
  mode,
  connected,
  connecting,
  userKey,
  onModeChange,
  onToggleConnection,
  onSelectServices,
}: MainScreenProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!connected) {
      setElapsed(0);
      return;
    }
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, [connected]);

  const shortId = userKey.replace(/\s/g, "").slice(0, 8);

  return (
    <div className="content">
      <button
        className={`power-btn ${connected ? "connected" : ""} ${connecting ? "connecting" : ""}`}
        onClick={onToggleConnection}
        title={connected ? "Отключить" : "Подключить"}
      >
        {connected ? (
          <span className="power-timer">{formatTimer(elapsed)}</span>
        ) : (
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18.36 6.64a9 9 0 11-12.73 0" />
            <line x1="12" y1="2" x2="12" y2="12" />
          </svg>
        )}
      </button>

      <p className="mode-label">Выберите режим работы:</p>
      <div className="mode-toggle">
        <button
          className={`mode-option ${mode === "combined" ? "active" : ""}`}
          onClick={() => onModeChange("combined")}
        >
          Комбинированный
        </button>
        <button
          className={`mode-option ${mode === "full" ? "active" : ""}`}
          onClick={() => onModeChange("full")}
        >
          Полный
        </button>
      </div>

      <p className="mode-description">{descriptions[mode]}</p>

      {mode === "combined" && (
        <button className="action-btn" onClick={onSelectServices}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="4" y1="21" x2="4" y2="14" />
            <line x1="4" y1="10" x2="4" y2="3" />
            <line x1="12" y1="21" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12" y2="3" />
            <line x1="20" y1="21" x2="20" y2="16" />
            <line x1="20" y1="12" x2="20" y2="3" />
            <line x1="1" y1="14" x2="7" y2="14" />
            <line x1="9" y1="8" x2="15" y2="8" />
            <line x1="17" y1="16" x2="23" y2="16" />
          </svg>
          Выбрать сервисы
        </button>
      )}

      <div className="status-bar">
        {connected && (
          <div className="status-pill">
            <span>📶</span>
            <span className="ping">28 ms</span>
            <span>ID: {shortId}…</span>
          </div>
        )}
        <p className="status-text" style={{ margin: 0 }}>
          {connecting ? "Подключение..." : connected ? "Подключено" : "Отключено"}
        </p>
      </div>
    </div>
  );
}
