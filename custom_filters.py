from aiogram.filters import BaseFilter

from config import ADMIN_IDS


class IsAdmin(BaseFilter):
    async def __call__(self, event) -> bool:
        return event.from_user.id in ADMIN_IDS
