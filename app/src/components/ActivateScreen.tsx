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
        <h2>InetFix</h2>
        <p>
          Введите ключ активации из Telegram-бота.
          <br />
          Получить ключ в Telegram: @Seb0g1
        </p>
        <input
          className="key-input"
          placeholder="XXXX XXXX XXXX XXXX"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          maxLength={19}
        />
        {error && <p className="error-text">{error}</p>}
        <button className="btn-primary" style={{ width: "100%" }} onClick={handleSubmit} disabled={loading}>
          {loading ? "Проверка..." : "Активировать"}
        </button>
      </div>
    </div>
  );
}
