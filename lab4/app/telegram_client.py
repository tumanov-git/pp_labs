from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging

from telethon import TelegramClient, functions, types
from telethon.sessions import SQLiteSession
from telethon.errors import RPCError


logger = logging.getLogger(__name__)


@dataclass
class TelegramAuth:
    api_id: int
    api_hash: str
    session_file: Path


class TelegramClientWrapper:
    """High-level Telethon operations with robust error handling.

    Uses a SQLiteSession stored in a .session file managed by Telethon.
    """

    def __init__(self, auth: TelegramAuth) -> None:
        self.auth = auth
        self._client: Optional[TelegramClient] = None

    async def _ensure_client(self) -> TelegramClient:
        if self._client is not None:
            return self._client

        session_path = self.auth.session_file
        logger.debug("🟢 Инициализация TelegramClient с SQLiteSession: %s", session_path)
        logger.debug("Файл сессии (полный путь): %s", str(session_path))
        try:
            exists = session_path.exists()
            size = session_path.stat().st_size if exists else 0
        except Exception:
            exists, size = False, 0
        logger.debug("Файл сессии существует: %s размер=%s", exists, size)
        # Ensure session directory exists
        try:
            session_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:  # noqa: BLE001
            logger.debug("Could not create session directory: %s", session_path.parent, exc_info=True)

        client = TelegramClient(
            SQLiteSession(str(session_path)),
            self.auth.api_id,
            self.auth.api_hash,
            system_version="4.16.30-vxCUSTOM",
            device_model="Desktop",
            app_version="1.0.0",
        )
        await client.connect()
        logger.debug("🔌 Клиент подключён к Telegram DC")
        is_auth = await client.is_user_authorized()
        logger.debug("🔐 is_user_authorized() = %s", is_auth)
        if not is_auth:
            try:
                me = await client.get_me()
                logger.debug("get_me(): %s", me)
            except Exception as e:  # noqa: BLE001
                logger.debug("get_me() ошибка: %s", e)
            logger.warning("Сессия не авторизована. Подсказка: выполните `python -m app.cli login --phone +7...`")
        self._client = client
        return client

    async def ensure_login(self, phone: str) -> None:
        """Interactive login to initialize a session.

        The session string is stored on disk. This should be called once on first
        setup. Subsequent runs will reuse the saved session.
        """
        logger.info("🔑 Запуск интерактивного логина для номера: %s", phone)
        session_path = self.auth.session_file
        # Ensure session directory exists
        try:
            session_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:  # noqa: BLE001
            logger.debug("Не удалось создать директорию для сессии: %s", session_path.parent, exc_info=True)
        client = TelegramClient(
            SQLiteSession(str(session_path)),
            self.auth.api_id,
            self.auth.api_hash,
            system_version="4.16.30-vxCUSTOM",
            device_model="Desktop",
            app_version="1.0.0",
        )
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            code = input("Enter the login code you received: ")
            try:
                await client.sign_in(phone=phone, code=code)
            except Exception:
                # Fallback for accounts with password (2FA)
                password = input("Two-step verification password: ")
                await client.sign_in(password=password)

        me = await client.get_me()
        logger.info("✅ Авторизовано как %s (%s)", getattr(me, "username", None), me.id)
        await client.disconnect()
        logger.info("💾 Сессия Telegram сохранена в %s", session_path)

    # Removed fallback methods to ensure a single, explicit wallpaper operation path

    async def apply_wallpaper(self, chat: str, path: Path, allow_set_channel_photo: bool) -> None:
        """Apply chat wallpaper via messages.SetChatWallPaperRequest only.

        No fallbacks. Raises on failure.
        """
        client = await self._ensure_client()
        if not await client.is_user_authorized():
            raise RuntimeError("Telegram session is not authorized. Check TELEGRAM_SESSION path or re-run login.")

        # Pre-validate file
        if not path.exists():
            raise FileNotFoundError(f"Wallpaper file not found: {path}")
        try:
            size = path.stat().st_size
        except Exception:
            size = 0
        logger.debug("Применяем обои к %s: %s (размер=%s)", chat, path, size)

        try:
            peer = await client.get_entity(chat)
            upload = await client.upload_file(str(path))
            suffix = path.suffix.lower()
            mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
            # Always use account.UploadWallPaperRequest then reference by id/hash
            wp_obj = await client(
                functions.account.UploadWallPaperRequest(
                    file=upload,
                    mime_type=mime,
                    settings=types.WallPaperSettings(
                        blur=False,
                        motion=False,
                        background_color=0,
                        intensity=100,
                    ),
                )
            )
            try:
                logger.debug("Результат UploadWallPaper: %s", wp_obj.stringify())
            except Exception:
                logger.debug("Результат UploadWallPaper: %s", wp_obj)
            wallpaper = types.InputWallPaper(id=wp_obj.id, access_hash=wp_obj.access_hash)
            result = await client(
                functions.messages.SetChatWallPaperRequest(
                    peer=peer,
                    wallpaper=wallpaper,
                    for_both=False,
                    revert=False,
                )
            )
            # Пытаемся удалить сервисное сообщение об изменении обоев
            try:
                if hasattr(result, "updates"):
                    for upd in result.updates:
                        msg = getattr(upd, "message", None)
                        action = getattr(msg, "action", None) if msg else None
                        if action and action.__class__.__name__ == "MessageActionSetChatWallPaper":
                            await client.delete_messages(peer, getattr(msg, "id", None))
                            break
            except Exception:
                # Тихий best-effort клинап
                pass
            logger.info("Обои успешно применены к %s", chat)
        except RPCError as exc:
            logger.error("Не удалось применить обои для %s: %s", chat, exc)
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("Неожиданная ошибка при применении обоев для %s: %s", chat, exc)
            raise

    async def close(self) -> None:
        if self._client:
            logger.debug("🔌 Отключаем Telegram-клиент и сохраняем сессию...")
            await self._client.disconnect()
            self._client = None