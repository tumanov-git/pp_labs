from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from telethon import TelegramClient, functions, types
from telethon.sessions import SQLiteSession


@dataclass
class TelegramAuth:
    api_id: int
    api_hash: str
    session_file: Path


class TelegramClientWrapper:
    def __init__(self, auth: TelegramAuth) -> None:
        self.auth = auth
        self._client: Optional[TelegramClient] = None

    async def _client_ready(self) -> TelegramClient:
        if self._client is not None:
            return self._client
        sp = self.auth.session_file
        sp.parent.mkdir(parents=True, exist_ok=True)
        c = TelegramClient(SQLiteSession(str(sp)), self.auth.api_id, self.auth.api_hash)
        await c.connect()
        self._client = c
        return c

    async def ensure_login(self, phone: str) -> None:
        sp = self.auth.session_file
        sp.parent.mkdir(parents=True, exist_ok=True)
        c = TelegramClient(SQLiteSession(str(sp)), self.auth.api_id, self.auth.api_hash)
        await c.connect()
        if not await c.is_user_authorized():
            await c.send_code_request(phone)
            code = input("Code: ")
            try:
                await c.sign_in(phone=phone, code=code)
            except Exception:
                pwd = input("Password: ")
                await c.sign_in(password=pwd)
        await c.disconnect()

    async def apply_wallpaper(self, chat: str, path: Path, allow_set_channel_photo: bool) -> None:
        c = await self._client_ready()
        if not await c.is_user_authorized():
            raise RuntimeError("not authorized")
        peer = await c.get_entity(chat)
        upload = await c.upload_file(str(path))
        mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        wp = await c(functions.account.UploadWallPaperRequest(file=upload, mime_type=mime, settings=types.WallPaperSettings(intensity=100)))
        inp = types.InputWallPaper(id=wp.id, access_hash=wp.access_hash)
        await c(functions.messages.SetChatWallPaperRequest(peer=peer, wallpaper=inp, for_both=False, revert=False))

    async def close(self) -> None:
        if self._client is None:
            return
        await self._client.disconnect()
        self._client = None


