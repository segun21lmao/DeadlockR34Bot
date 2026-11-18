import html
import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from keyboards import admin_kb
from states import Offer

log = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Пришли мне свой пост (текст, фото, видео), и я передам его админам."
    )
    await state.set_state(Offer.waiting_content)


@router.message(Offer.waiting_content)
async def handle_offer(message: Message, state: FSMContext, bot: Bot) -> None:
    if not message.from_user:
        return

    # Экранируем имя, чтобы спецсимволы (<, >, &) не ломали HTML-разметку
    safe_name = html.escape(message.from_user.full_name)
    who = safe_name
    if message.from_user.username:
        who += f" (@{message.from_user.username})"

    origin_chat_id = message.chat.id
    origin_msg_id = message.message_id

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"📩 <b>Новый оффер</b>\nОт: {who}\nID: {message.from_user.id}",
                parse_mode="HTML",
                reply_markup=admin_kb(origin_chat_id, origin_msg_id),
            )
            await message.copy_to(chat_id=admin_id)
        except Exception as e:
            log.exception("Не смог уведомить админа %s: %s", admin_id, e)

    await message.answer("✅ Отправлено на модерацию.\n\nЖду следующий пост.")
    await state.clear()
