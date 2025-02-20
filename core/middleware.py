
import json
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from . import database
from .config import dp


class BasicMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        message = event.message or event.callback_query.message
        user = await database.get_user(message.chat.id)
        if not user:
            await database.add_user(message.chat.id)
            user = await database.get_user(message.chat.id)

        data['user'] = user
        return await handler(event, data)
