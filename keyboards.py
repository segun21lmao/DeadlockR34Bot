from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_kb(chat_id: int, message_id: int) -> InlineKeyboardMarkup:
    """Кнопки под уведомлением для админа."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=f"accept:{chat_id}:{message_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"reject:{chat_id}:{message_id}"
                )
            ],
        ]
    )
