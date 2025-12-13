from __future__ import annotations

import argparse
import asyncio
import os
import time
from pathlib import Path
import logging

from . import setup_logging
from .config import Config
from .service import AppService
from .log_utils import rebuild_weather_stats_from_log


def _args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="tgwall")
    sub = p.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--city", default=None)
    r = sub.add_parser("run", parents=[common]); r.add_argument("--log-level", default=None)
    d = sub.add_parser("daemon", parents=[common]); d.add_argument("--interval", type=int, default=None); d.add_argument("--log-level", default=None)
    l = sub.add_parser("login", parents=[common]); l.add_argument("--phone", required=True); l.add_argument("--log-level", default=None)
    t = sub.add_parser("test-wallpaper", parents=[common]); t.add_argument("--image", required=True); t.add_argument("--log-level", default=None)
    s = sub.add_parser("stats-rebuild", parents=[common]); s.add_argument("--log-file", default=None); s.add_argument("--log-level", default=None)
    return p.parse_args()


def main() -> None:
    a = _args()
    setup_logging(log_level=a.log_level or os.getenv("LOG_LEVEL", "INFO"), log_dir=Path("logs"))
    cfg = Config.load()
    os.environ["TZ"] = cfg.core.tz
    if hasattr(time, "tzset"):
        time.tzset()
    logging.getLogger("telethon").setLevel(logging.INFO)
    svc = AppService(cfg)
    if a.cmd == "run":
        asyncio.run(svc.run_once(city=a.city))
        return
    if a.cmd == "daemon":
        asyncio.run(svc.run_daemon(interval_minutes=a.interval, city=a.city))
        return
    if a.cmd == "login":
        from .telegram_client import TelegramAuth, TelegramClientWrapper
        tcfg = cfg.telegram
        w = TelegramClientWrapper(TelegramAuth(tcfg.api_id, tcfg.api_hash, tcfg.session_file))
        asyncio.run(w.ensure_login(a.phone))
        return
    if a.cmd == "test-wallpaper":
        from .telegram_client import TelegramAuth, TelegramClientWrapper
        tcfg = cfg.telegram
        w = TelegramClientWrapper(TelegramAuth(tcfg.api_id, tcfg.api_hash, tcfg.session_file))
        asyncio.run(w.apply_wallpaper(tcfg.chat, Path(a.image).expanduser().resolve(), tcfg.allow_set_channel_photo))
        return
    base = cfg.config_dir.parent
    log_path = Path(a.log_file).expanduser().resolve() if a.log_file else (base / "logs" / "weather.log")
    out = base / ".cache" / "weather_stats.json"
    rebuild_weather_stats_from_log(log_path, out)


if __name__ == "__main__":
    main()


