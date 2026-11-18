import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from config import CHANNEL_ID
from custom_filters import IsAdmin

log = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith("accept:"), IsAdmin())
async def on_accept(call: CallbackQuery, bot: Bot) -> None:
    """Публикуем сразу: copy_message из исходного чата в канал."""
    if not call.data:
        return

    _, chat_id, message_id = call.data.split(":")
    try:
        await bot.copy_message(
            chat_id=CHANNEL_ID,
            from_chat_id=int(chat_id),
            message_id=int(message_id),
        )
        if isinstance(call.message, Message):
            current_text = call.message.text or ""
            await call.message.edit_text(f"{current_text}\n\n✅ Опубликовано.")
        await call.answer("Опубликовано")
    except Exception as e:
        # Частая причина: пользователь удалил свой пост до модерации.
        log.exception("Публикация упала: %s", e)
        await call.answer(f"Ошибка публикации: {e}", show_alert=True)


@router.callback_query(F.data.startswith("reject:"), IsAdmin())
async def on_reject(call: CallbackQuery) -> None:
    if isinstance(call.message, Message):
        current_text = call.message.text or ""
        await call.message.edit_text(f"{current_text}\n\n❌ Отклонено.")
    await call.answer("Отклонено")
