# v2ex_feed/settings.py
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # v2ex_feed/../../ → 项目根
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    # === 通用 ===
    LOG_LEVEL: str = "INFO"  # DEBUG / INFO / WARNING / ERROR / CRITICAL
    TIMEZONE: str = "Asia/Shanghai"

    # === 程序业务 ===
    RSS_URL: str  # 必填，缺失会抛 ValidationError
    FETCH_INTERVAL: int = 6  # 抓取间隔（秒）

    # === 数据库 ===
    DB_FILE: str = "v2ex.db"

    # === Telegram ===
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    # === Worker ===
    WORKER_NUM: int = 1

    # Pydantic v2 的配置写在 model_config 里
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
