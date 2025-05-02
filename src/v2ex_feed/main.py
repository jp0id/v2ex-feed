# main.py
import asyncio

from loguru import logger

from v2ex_feed.logger_cfg import init_logger
from v2ex_feed.models import init_db
from v2ex_feed.queueing import send_worker, send_queue
from v2ex_feed.rss_tasks import start_scheduler
from v2ex_feed.settings import settings


async def main() -> None:
    init_logger(level=settings.LOG_LEVEL)
    await init_db()
    start_scheduler()

    workers = [asyncio.create_task(send_worker(i)) for i in range(settings.WORKER_NUM)]

    logger.info("主循环启动，按 Ctrl-C 退出")
    try:
        await asyncio.gather(*workers)
    except (KeyboardInterrupt, SystemExit):
        logger.info("收到退出信号，等待队列清空…")
        await send_queue.join()
