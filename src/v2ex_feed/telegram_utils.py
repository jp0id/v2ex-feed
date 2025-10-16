import asyncio
import html
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from aiolimiter import AsyncLimiter
from dateutil import tz
from loguru import logger
from telegram import Bot, constants, LinkPreviewOptions
from telegram.error import RetryAfter, TelegramError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from v2ex_feed.settings import settings

TIMEZONE = settings.TIMEZONE
TELEGRAM_BASE_URL = settings.TELEGRAM_BASE_URL
SHANGHAI_TZ = tz.gettz(TIMEZONE)


# ---------------- 数据类 ----------------
@dataclass(slots=True, frozen=True)
class PostPayload:
    """所有可用于推送的字段"""
    title: str
    link: str
    node_name: Optional[str] = None
    content: Optional[str] = None
    published: Optional[datetime] = None
    updated: Optional[datetime] = None
    author_name: Optional[str] = None
    author_uri: Optional[str] = None

    def _fmt_published(self) -> Optional[str]:
        """
        把发布时间统一格式化成本地时区字符串，并附加周几
        """
        if not self.published:
            return None
        dt = self.published
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz.UTC)
        local_dt = dt.astimezone(SHANGHAI_TZ)
        # 定义中文周映射：Monday=0
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        weekday = weekdays[local_dt.weekday()]
        # 返回格式：YYYY-MM-DD HH:MM:SS 周X
        return local_dt.strftime("%Y-%m-%d %H:%M:%S") + f" 周{weekday}"

    def to_html(self) -> str:
        """渲染成 Telegram HTML 消息（parse_mode='HTML'）"""

        header = f"<b>{html.escape(self.title)}</b>"

        body = (
            f"<blockquote expandable>{self.content}</blockquote>"
            if self.content else
            '<blockquote expandable>[此贴没有内容～]</blockquote>'
        )

        author_line = f'👤 <a href="{self.author_uri}">{html.escape(self.author_name)}</a>' if self.author_name else None

        if self.node_name:
            raw = "".join(self.node_name.split()).replace("#", "")
            tag = html.escape(raw).strip()
            node_line = f"🏷️ #{tag} {settings.TELEGRAM_CHAT_USERNAME}"
        else:
            node_line = None

        time_line = f"🕒 {self._fmt_published()}" if self.published else None
        link_line = f'🔗 <a href="{self.link}">阅读原帖</a>' if self.link else None

        parts = [
            header,
            "",
            body,
            "",
            author_line,
            node_line,
            time_line,
            link_line,
        ]

        return "\n".join(p for p in parts if p is not None)


bot = Bot(settings.TELEGRAM_BOT_TOKEN,
          base_url="f{TELEGRAM_BASE_URL}/bot",
          base_file_url="f{TELEGRAM_BASE_URL}/file/bot")

limiter_fast = AsyncLimiter(1, 3)  # 每 3 s 1 条
limiter_minute = AsyncLimiter(20, 60)  # 每 60 s 20 条


@retry(
    retry=retry_if_exception_type((RetryAfter, TelegramError)),
    stop=stop_after_attempt(3),  # 最多重试 3 次
    wait=wait_exponential_jitter(initial=1, max=30),  # 仅对非 RetryAfter 生效
    reraise=True,
)
async def _safe_send(payload: PostPayload) -> None:
    """真正与 Telegram API 交互，附带限流 + Flood 控制"""
    async with limiter_fast, limiter_minute:
        try:
            logger.info(f"bot base url: {bot.base_url}")
            logger.info(f"bot base file url: {bot.base_file_url}")
            await bot.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                text=payload.to_html(),
                parse_mode=constants.ParseMode.HTML,
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
            logger.debug("Telegram 推送成功")
        except RetryAfter as e:
            # Flood control：官方返回 e.retry_after 秒
            wait = e.retry_after + 0.5  # 加 0.5 s buffer
            logger.warning(f"Flood 控制，等待 {wait:.1f}s 再试…")
            await asyncio.sleep(wait)
            raise  # 交给 tenacity 进入下一 attempt
        except TelegramError as e:
            logger.error(f"TelegramError：{e}")
            raise


async def send_post(payload: PostPayload) -> None:
    """
    外部调用入口：限流 / 重试 / 日志
    """
    try:
        logger.debug(f"准备发送消息，标题: {payload.title}")
        await _safe_send(payload)
    except Exception as e:
        logger.error(f"发送 Telegram 消息失败：{e} | 数据：{asdict(payload)}")
        raise
