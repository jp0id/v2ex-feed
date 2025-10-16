# v2ex_feed/rss_tasks.py
from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

import aiohttp
import feedparser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dateutil import parser as date_parser, tz
from loguru import logger
from tortoise.transactions import atomic

from models import Post
from queueing import send_queue  # ★ 新：异步发送队列
from settings import settings
from telegram_html_formatter import html_to_telegram
from telegram_utils import PostPayload  # 仍需数据类

# ---------- 常量 ----------
TIMEZONE = settings.TIMEZONE
SHANGHAI_TZ = tz.gettz(TIMEZONE)
etag_cache: str | None = None


# ---------- 工具函数 ----------
def parse_utc_to_local(utc_str: str) -> datetime | None:
    if not utc_str:
        return None
    dt = date_parser.parse(utc_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz.UTC)
    return dt.astimezone(SHANGHAI_TZ)


def extract_node_name(title: str) -> str | None:
    m = re.search(r"\[(.+?)]", title or "")
    return m.group(1).strip() if m else None


def clean_title(title: str) -> str:
    title = re.sub(r"\s*\[.*?]\s*", " ", title or "", count=1)
    return re.sub(r"\s+", " ", title).strip()


def extract_v2ex_id(entry_id: str) -> str | None:
    m = re.search(r"/t/(\d+)", entry_id or "")
    return m.group(1) if m else None


def clean_link(link: str) -> str:
    return urlparse(link)._replace(fragment="").geturl() if link else ""


# ---------- 抓取 ----------
async def fetch_rss(session: aiohttp.ClientSession) -> bytes | None:
    global etag_cache
    headers = {"If-None-Match": etag_cache} if etag_cache else {}
    logger.info("请求 RSS 源…")
    async with session.get(settings.RSS_URL, headers=headers) as resp:
        if resp.status == 304:
            logger.debug("无新内容（304）")
            return None
        resp.raise_for_status()
        etag_cache = resp.headers.get("ETag")
        return await resp.read()


# ---------- 入库 + 入队（事务） ----------
@atomic()
async def save_and_enqueue(entry) -> None:
    """把 RSS 条目写库，未推送的放入 send_queue"""
    vid = extract_v2ex_id(entry.id)
    if not vid:
        logger.warning(f"未能解析 v2ex_id：{entry.id}")
        return

    post, created = await Post.get_or_create(
        v2ex_id=vid,
        defaults={
            "node_name": extract_node_name(entry.title),
            "title": clean_title(entry.title),
            "link": clean_link(entry.link),
            "content": entry.content[0].value.strip() if "content" in entry and entry.content[
                0].value.strip() else None,
            "published": parse_utc_to_local(entry.get("published", "")),
            "updated": parse_utc_to_local(entry.get("updated", "")),
            "author_name": entry.get("author"),
            "author_uri": entry.get("author_detail", {}).get("href"),
            "created_at": datetime.now(SHANGHAI_TZ),
            "updated_at": datetime.now(SHANGHAI_TZ),
            "sent": False,
        },
    )

    if not created and post.sent:
        logger.debug(f"已推送过，跳过：{vid}")
        return

    payload = PostPayload(
        title=post.title,
        link=post.link,
        node_name=post.node_name,
        content=html_to_telegram(post.content),
        published=post.published,
        updated=post.updated,
        author_name=post.author_name,
        author_uri=post.author_uri,
    )

    await send_queue.put(payload)  # ★ 只排队，不直接发
    logger.info(f"已入队等待推送：{payload.title}")

    post.sent = True  # 先标记，避免重复排队
    await post.save(update_fields=["sent"])


# ---------- 主循环 ----------
async def process_rss():
    async with aiohttp.ClientSession() as session:
        content = await fetch_rss(session)
        if not content:
            return
        feed = feedparser.parse(content)

        # ---------- 仅按 published 升序 ----------
        def _published_dt(item) -> datetime:
            """解析 <published>，无则排到最后"""
            value = item.get("published")
            if not value:
                return datetime.max.replace(tzinfo=tz.UTC)

            dt = date_parser.parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz.UTC)
            return dt.astimezone(tz.UTC)

        sorted_entries = sorted(feed.entries, key=_published_dt)
        logger.info(f"解析到 {len(sorted_entries)} 条条目（已按 published 升序）")

        for entry in sorted_entries:  # 早 → 晚依次入队
            try:
                await save_and_enqueue(entry)
            except Exception as e:
                logger.exception(f"条目处理失败：{e}")


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        process_rss,
        "interval",
        seconds=settings.FETCH_INTERVAL,
        max_instances=2,
        coalesce=True,
        misfire_grace_time=30,
    )
    scheduler.start()
    logger.info(f"定时任务已启动，每 {settings.FETCH_INTERVAL} 秒抓取一次 RSS。")
