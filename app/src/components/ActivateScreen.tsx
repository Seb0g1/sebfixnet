import { useState } from "react";
import { validateKey } from "../services/api";

interface ActivateScreenProps {
  apiUrl: string;
  onActivated: (key: string) => void;
}

export function ActivateScreen({ apiUrl, onActivated }: ActivateScreenProps) {
  const [key, setKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const formatKeyInput = (value: string) => {
    const digits = value.replace(/\D/g, "").slice(0, 16);
    return digits.replace(/(\d{4})(?=\d)/g, "$1 ").trim();
  };

  const handleSubmit = async () => {
    setError("");
    const cleaned = key.replace(/\s/g, "");
    if (cleaned.length !== 16 || !/^\d+$/.test(cleaned)) {
      setError("Введите 16-значный ключ из Telegram-бота");
      return;
    }

    setLoading(true);
    try {
      const formatted = cleaned.replace(/(\d{4})/g, "$1 ").trim();
      await validateKey(formatted, apiUrl);
      onActivated(formatted);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка активации");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="content">
      <div className="activate-form">
        <div className="activate-card">
          <img src="/logo.png" alt="FixInet.ez" className="brand-logo" />
          <div className="brand-title">FixInet.ez</div>
          <div className="brand-sub">By Seb0g1</div>
          <p>
            Введите ключ активации из Telegram-бота.
            <br />
            Каждый пользователь получает свой уникальный ключ.
          </p>
          <input
            className="key-input"
            placeholder="XXXX XXXX XXXX XXXX"
            value={key}
            onChange={(e) => setKey(formatKeyInput(e.target.value))}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            maxLength={19}
            autoFocus
          />
          {error && <p className="error-text">{error}</p>}
          <button
            className="btn-primary"
            style={{ width: "100%" }}
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? "Проверка..." : "Активировать"}
          </button>
        </div>
        <p className="footer-hint">
          Получить ключ: <a href="https://t.me/Seb0g1" target="_blank" rel="noreferrer">Telegram-бот</a>
        </p>
      </div>
    </div>
  );
}
