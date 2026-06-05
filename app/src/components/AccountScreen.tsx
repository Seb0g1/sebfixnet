import type { AppSettings } from "../types";
import { copyToClipboard } from "../services/tauri";

interface AccountScreenProps {
  settings: AppSettings;
  onChange: (partial: Partial<AppSettings>) => void;
  onLogout: () => void;
  onBack: () => void;
  onSave: () => void;
}

const AUTOSTART_OPTIONS = [
  { value: "none", label: "Не запускать приложение автоматически" },
  { value: "app_only", label: "Только запустить приложение (без подключения)" },
  { value: "combined", label: "Запустить и подключиться в комбинированном режиме" },
  { value: "full", label: "Запустить и подключиться в полном режиме" },
  { value: "last", label: "Запустить и подключиться в последнем использованном режиме" },
];

export function AccountScreen({
  settings,
  onChange,
  onLogout,
  onBack,
  onSave,
}: AccountScreenProps) {
  const formattedKey = settings.key
    ? settings.key.replace(/(\d{4})(?=\d)/g, "$1 ").trim()
    : "—";

  return (
    <div className="content">
      <h2 className="screen-title">Аккаунт</h2>

      <div className="account-section">
        <div className="account-row">
          <span className="account-label">Тариф:</span>
          <span className="account-value pro">FREE</span>
        </div>
        <div className="account-row">
          <span className="account-label">Ключ:</span>
          <div className="key-row">
            <span className="account-value key-value">{formattedKey}</span>
            {settings.key && (
              <button
                className="icon-btn"
                style={{ width: 28, height: 28 }}
                onClick={() => copyToClipboard(settings.key)}
                title="Копировать"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" />
                  <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      <button className="danger-btn" onClick={onLogout}>
        Выйти из аккаунта
      </button>

      <div className="account-section">
        <h3 className="section-title">Автозапуск и подключение</h3>
        <div className="radio-group">
          {AUTOSTART_OPTIONS.map((opt) => (
            <label key={opt.value} className="radio-item">
              <input
                type="radio"
                name="autostart"
                checked={settings.autostart === opt.value}
                onChange={() => onChange({ autostart: opt.value })}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      <div className="account-section">
        <h3 className="section-title">Поведение окна</h3>
        <div className="checkbox-group">
          <label className="checkbox-item">
            <input
              type="checkbox"
              checked={settings.minimizeOnStart}
              onChange={(e) => onChange({ minimizeOnStart: e.target.checked })}
            />
            Сворачивать в трей при запуске
          </label>
          <label className="checkbox-item">
            <input
              type="checkbox"
              checked={settings.minimizeOnClose}
              onChange={(e) => onChange({ minimizeOnClose: e.target.checked })}
            />
            Сворачивать в трей при закрытии окна
          </label>
        </div>
      </div>

      <div className="footer-btns">
        <button className="btn-secondary" onClick={onBack}>
          Отмена
        </button>
        <button className="btn-primary" onClick={onSave}>
          Сохранить изменения
        </button>
      </div>
    </div>
  );
}
