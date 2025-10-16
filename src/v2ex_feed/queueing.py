# v2ex_feed/queueing.py
import asyncio

from loguru import logger

from telegram_utils import send_post, limiter_fast, limiter_minute

#: 全局异步队列，容量 1000 足够
send_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)

#: 后台 worker 的核心协程
async def send_worker(worker_id: int) -> None:
    logger.info(f"发送 worker-{worker_id} 启动…")
    while True:
        payload = await send_queue.get()          # 阻塞直到有数据
        try:
            async with limiter_fast, limiter_minute:
                await send_post(payload)
                logger.debug(f"✅ worker-{worker_id} 成功推送: {payload.title}")
        except Exception as e:
            # 这里已经有 telegram_utils 的 retry，仍失败就记录死信
            logger.exception(f"❌ worker-{worker_id} 彻底失败: {e} | {payload.title}")
        finally:
            send_queue.task_done()
