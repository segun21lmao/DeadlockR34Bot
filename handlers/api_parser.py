import asyncio
import html
import json
import logging
import os

import aiohttp
from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from dotenv import load_dotenv

from config import ADMIN_IDS, TAGS_DICT
from custom_filters import IsAdmin
from keyboards import admin_kb

log = logging.getLogger(__name__)
router = Router()
load_dotenv()
key = os.getenv("API_KEY")


@router.message(Command("fetch"), IsAdmin())
async def fetch_cmd(message: Message, command: CommandObject, bot: Bot):
    if not command.args or not command.args.isdigit():
        await message.answer("Укажите число постов, например: /fetch 3")
        return

    posts = await fetch_posts(int(command.args))
    if not posts:
        await message.answer("Ничего не найдено.")
        return

    for post in posts:
        if not isinstance(post, dict):
            continue

        file_url = post.get("file_url")
        if not file_url:
            continue

        # 1. Формируем переменную context с тегами (обрезаем и экранируем для безопасности HTML)
        raw_tags = post.get("tags", "")
        log.warning(
            "DEBUG POST %s | type=%s | tags=%r",
            post.get("id"),
            type(raw_tags),
            raw_tags,
        )
        base_context = parse_tags(raw_tags, TAGS_DICT)
        context_tail = (
            "\n\n" + '<a href="https://t.me/+-kpN7m2i80piOGMy">ПОДПИСАТЬСЯ</a>'
        )
        # 2. Отправляем файл в зависимости от его расширения
        clean_url = file_url.split("?")[0].lower()

        msg = None

        try:
            if clean_url.endswith((".mp4", ".webm")):
                context = html.escape(base_context + "#video") + context_tail
                msg = await message.answer_video(
                    video=file_url,
                    caption=context,
                    parse_mode="HTML",
                    request_timeout=60,
                )
            elif clean_url.endswith(".gif"):
                context = html.escape(base_context + "#gif") + context_tail
                msg = await message.answer_animation(
                    animation=file_url,
                    caption=context,
                    parse_mode="HTML",
                    request_timeout=60,
                )
            else:
                context = html.escape(base_context.strip()) + context_tail
                msg = await message.answer_photo(
                    photo=file_url,
                    caption=context,
                    parse_mode="HTML",
                    request_timeout=60,
                )

        except TelegramRetryAfter as e:
            log.warning("Флуд-контроль Telegram, ждем %s сек.", e.retry_after)
            await asyncio.sleep(e.retry_after + 1)
            continue

        except TelegramBadRequest as e:
            log.warning(
                "BadRequest для %s (%s), пробуем сжатую версию...",
                file_url,
                e.message,
            )
            sample_url = post.get("sample_url")
            if sample_url and sample_url != file_url:
                try:
                    context = html.escape(base_context.strip())
                    msg = await message.answer_photo(
                        photo=sample_url,
                        caption=context,
                        parse_mode="HTML",
                        request_timeout=60,
                    )
                except Exception as err:
                    log.error("Не удалось отправить даже sample_url: %s", err)
                    continue
            else:
                continue

        if not msg:
            continue

        origin_chat_id = msg.chat.id
        origin_msg_id = msg.message_id

        # 3. Уведомляем админов с небольшими паузами
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    "📩 <b>Новый оффер пост</b>",
                    parse_mode="HTML",
                    reply_markup=admin_kb(origin_chat_id, origin_msg_id),
                )

                if admin_id != origin_chat_id:
                    await msg.copy_to(chat_id=admin_id)

                await asyncio.sleep(0.3)
            except Exception as e:
                log.exception("Не смог уведомить админа %s: %s", admin_id, e)

        # Таймаут между постами, чтобы избежать BadRequest / FloodWait при множественном вызове
        await asyncio.sleep(1.5)


def parse_tags(raw_tags: str, tags_dict: dict) -> str:
    # Разбиваем строку тегов поста по пробелам и приводим к нижнему регистру
    post_tags = set(raw_tags.lower().split())

    hashtags = [
        hashtag
        for r34_tags, hashtag in tags_dict.items()
        if any(tag.lower() in post_tags for tag in r34_tags)
    ]

    result = " ".join(hashtags)
    return f"{result} " if result else ""


async def fetch_posts(post_limit: int) -> list:
    # Используем официальный путь к API согласно документации
    url = "https://api.rule34.xxx"
    params = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "tags": "deadlock -ai_generated -1boy -fart -fart_fetish -futa_only -futanari -guro -hyper_ass -male_only -pregnancy -pregnant -super_belly",
        "limit": post_limit,
        "json": 1,
        "api_key": str(key),
        "user_id": 4769647,
    }
    headers = {"User-Agent": "MyCustomApp/1.0"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as response:
            text = await response.text()

            if response.status != 200 or not text.strip():
                log.error("Ошибка API (%s): %s", response.status, text[:200])
                return []

            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                log.error("Невалидный JSON от сервера: %s", text[:200])
                return []

            if not isinstance(data, list):
                log.error("API вернул неожиданный формат вместо списка: %s", data)
                return []

            return data
