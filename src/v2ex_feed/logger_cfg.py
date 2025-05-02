from loguru import logger
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def init_logger(level: str = "INFO") -> None:
    logger.remove()
    logger.add(
        LOG_DIR / "v2ex_{time:YYYYMMDD_HH}.log",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
               "PID:{process:<5} | {module}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level:<8}</level> | "
               "<cyan>{module}:{line}</cyan> - <level>{message}</level>",
        enqueue=True,
    )
