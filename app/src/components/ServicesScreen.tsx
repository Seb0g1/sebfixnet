import { useMemo, useState } from "react";
import { SERVICE_CATALOG } from "../services/catalog";

interface ServicesScreenProps {
  selected: string[];
  onToggle: (id: string) => void;
  onBack: () => void;
}

export function ServicesScreen({ selected, onToggle, onBack }: ServicesScreenProps) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return Object.entries(SERVICE_CATALOG).filter(([, info]) =>
      info.name.toLowerCase().includes(q)
    );
  }, [query]);

  return (
    <div className="content">
      <h2 className="screen-title">Выбор сервисов</h2>

      <div className="search-bar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          placeholder="Поиск"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="services-grid">
        {filtered.map(([id, info]) => (
          <div
            key={id}
            className={`service-card ${selected.includes(id) ? "selected" : ""}`}
            onClick={() => onToggle(id)}
          >
            <div className={`service-icon icon-${info.icon}`}>
              {info.name.charAt(0)}
            </div>
            <span className="service-name">{info.name}</span>
          </div>
        ))}
      </div>

      <p className="footer-hint" style={{ marginTop: 20 }}>
        Не нашли нужный сервис?{" "}
        <a href="https://t.me/Seb0g1" target="_blank" rel="noreferrer">
          Напишите нам
        </a>{" "}
        и мы добавим его!
      </p>

      <div className="footer-btns">
        <button className="btn-primary" onClick={onBack}>
          Готово ({selected.length})
        </button>
      </div>
    </div>
  );
}
