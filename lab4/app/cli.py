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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram TGWall CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config-dir", default=str(Path("config")), help="Path to config directory")
    common.add_argument("--city", default=None, help="Override city (default from .env.core)")

    p_run = sub.add_parser("run", parents=[common], help="Run a single update")
    p_run.add_argument("--log-level", default=None, help="Override log level")

    p_daemon = sub.add_parser("daemon", parents=[common], help="Run as daemon loop")
    p_daemon.add_argument("--interval", type=int, default=None, help="Override interval minutes")
    p_daemon.add_argument("--log-level", default=None, help="Override log level")

    p_login = sub.add_parser("login", parents=[common], help="Interactive login to Telegram")
    p_login.add_argument("--phone", required=True, help="Phone number for first login")
    p_login.add_argument("--log-level", default=None, help="Override log level")

    p_test = sub.add_parser("test-wallpaper", parents=[common], help="Test applying chat wallpaper with an image path")
    p_test.add_argument("--image", required=True, help="Path to image (.jpg/.png)")
    p_test.add_argument("--log-level", default=None, help="Override log level")

    p_stats = sub.add_parser("stats-rebuild", parents=[common], help="Rebuild weather stats from logs/weather.log")
    p_stats.add_argument("--log-file", default=None, help="Override weather log path (default: logs/weather.log)")
    p_stats.add_argument("--log-level", default=None, help="Override log level")

    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Setup logging early
    env_log_level = os.getenv("LOG_LEVEL", "DEBUG")
    setup_logging(log_level=args.log_level or env_log_level, log_dir=Path("logs"))
    # Tune third-party loggers
    logging.getLogger("telethon.network.mtprotosender").setLevel(logging.INFO)
    logging.getLogger("telethon").setLevel(logging.INFO)

    # Load and validate configuration before any service/client init
    try:
        cfg = Config.load()
    except ValueError as e:
        logging.error("Configuration error: %s", e)
        print("Fix your config/.env files. For testing, you can: export $(grep -v '^#' config/.env.telegram | xargs)")
        raise SystemExit(2)

    # Honor TZ from core config for local time operations
    os.environ["TZ"] = cfg.core.tz
    if hasattr(time, "tzset"):
        time.tzset()

    service = AppService(cfg)

    if args.command == "run":
        asyncio.run(service.run_once(city=args.city))
    elif args.command == "daemon":
        asyncio.run(service.run_daemon(interval_minutes=args.interval, city=args.city))
    elif args.command == "login":
        # Delayed import to avoid Telethon import if unused
        from .telegram_client import TelegramAuth, TelegramClientWrapper

        t = cfg.telegram
        wrapper = TelegramClientWrapper(TelegramAuth(t.api_id, t.api_hash, t.session_file))
        asyncio.run(wrapper.ensure_login(args.phone))
    elif args.command == "test-wallpaper":
        from .telegram_client import TelegramAuth, TelegramClientWrapper
        from pathlib import Path as _P
        t = cfg.telegram
        wrapper = TelegramClientWrapper(TelegramAuth(t.api_id, t.api_hash, t.session_file))
        image_path = _P(args.image).expanduser().resolve()
        if not image_path.exists():
            logging.error("Image not found: %s", image_path)
            raise SystemExit(2)
        try:
            asyncio.run(wrapper.apply_wallpaper(t.chat, image_path, t.allow_set_channel_photo))
            logging.info("Test wallpaper applied successfully.")
        except Exception as e:
            logging.error("Test wallpaper failed: %s", e)
            raise SystemExit(2)
    elif args.command == "stats-rebuild":
        base_dir = cfg.config_dir.parent
        log_path = Path(args.log_file).expanduser().resolve() if args.log_file else (base_dir / "logs" / "weather.log")
        stats_cfg = cfg.wallpaper_matrix.get("stats") or {}
        stats_file = str(stats_cfg.get("file", ".cache/weather_stats.json"))
        out_file = (base_dir / stats_file).expanduser().resolve()
        rebuild_weather_stats_from_log(log_path, out_file)
        logging.info("Stats rebuilt -> %s", out_file)
    else:
        raise SystemExit(2)


if __name__ == "__main__":
    main()