# sebfixnet

**Fixnet** — сервис стабильного доступа к Telegram, Discord, YouTube и другим приложениям.

- Сайт: https://fixnet.sebog1.ru
- Админка: https://fixnet.sebog1.ru/admin
- Канал: https://t.me/seb0g1site

## Стек

| Компонент | Путь |
|-----------|------|
| Лендинг | `website/` |
| Админ-панель | `admin/` |
| Backend API | `backend/` |
| Telegram-бот | `bot/` |
| Деплой | `server/deploy.sh` |

## Быстрый старт (локально)

```powershell
copy .env.example .env
# Заполните BOT_TOKEN, API_SECRET, ADMIN_PASSWORD
.\start-local.ps1
```

## Деплой на сервер

```bash
# На сервере (Ubuntu/Debian)
bash server/deploy.sh
```

Перед деплоем создайте `.env` на сервере (см. `.env.example`).

## Админ-панель

1. **Рассылка** — HTML, кнопки, премиум-эмодзи
2. **Канал** — автопересылка из @seb0g1site
3. **Поддержка** — ответы на тикеты
4. **Аналитика** — пользователи, ключи, рассылки

Бот должен быть администратором канала @seb0g1site.

## Автор

Seb0g1
