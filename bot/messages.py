from config import settings


def welcome_text() -> str:
    return (
        f"<b>Добро пожаловать в {settings.app_name}!</b>\n"
        f"<i>By {settings.app_author}</i>\n\n"
        "Стабилизатор интернет-соединения для обхода ограничений.\n\n"
        "Нажмите <b>«Подключить»</b>, чтобы получить бесплатный ключ активации "
        "и ссылку на скачивание приложения."
    )


def key_message(key: str, expires_at: str) -> str:
    exp = expires_at[:10] if expires_at else "—"
    return (
        f"<b>Добро пожаловать в {settings.app_name}!</b>\n"
        f"<i>By {settings.app_author}</i>\n\n"
        "Вы можете протестировать сервис и помочь нам стать лучше.\n\n"
        f"<b>Ваш ключ активации:</b>\n"
        f"<code>{key}</code>\n\n"
        f"<b>Ссылка для скачивания:</b>\n"
        f"{settings.download_url}\n\n"
        f"<b>Тариф:</b> FREE (до {exp})\n\n"
        "Если нашли баги или есть идеи — напишите в поддержку.\n"
        f"Поддержка: @{settings.support_username}\n"
        f"Новости: @{settings.channel_username}\n\n"
        "Остались вопросы? Нажмите /help"
    )


def help_text() -> str:
    return (
        f"<b>{settings.app_name} — инструкция</b>\n\n"
        "1. Нажмите <b>«Подключить»</b> и скопируйте ключ\n"
        "2. Скачайте приложение по ссылке из сообщения\n"
        "3. Установите Fixnet и введите ключ\n"
        "4. Выберите режим:\n"
        "   • <b>Комбинированный</b> — только выбранные сервисы\n"
        "   • <b>Полный</b> — весь трафик через сервер\n"
        "5. Нажмите кнопку питания для подключения\n\n"
        f"Поддержка: @{settings.support_username}"
    )
