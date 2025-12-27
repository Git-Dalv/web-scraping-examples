import random
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DELAY_MIN = 1.5
DELAY_MAX = 4.0
LONG_PAUSE_CHANCE = 0.05
LONG_PAUSE_MIN = 10
LONG_PAUSE_MAX = 30


async def human_delay(min_sec: float = DELAY_MIN, max_sec: float = DELAY_MAX):
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def gaussian_delay(base: float = 2.0, jitter: float = 0.5):
    delay = random.gauss(base, jitter)
    delay = max(0.5, delay)
    await asyncio.sleep(delay)


async def random_pause(chance: float = LONG_PAUSE_CHANCE,min_sec: float = LONG_PAUSE_MIN,max_sec: float = LONG_PAUSE_MAX):
    if random.random() < chance:
        pause = random.uniform(min_sec, max_sec)
        logger.debug(f"Taking a break: {pause:.1f}s")
        await asyncio.sleep(pause)


def get_time_multiplier() -> float:
    hour = datetime.now().hour

    if 2 <= hour <= 6:
        return 2.0
    elif 9 <= hour <= 17:
        return 0.8
    else:
        return 1.0


async def smart_delay(base_min: float = DELAY_MIN, base_max: float = DELAY_MAX):
    multiplier = get_time_multiplier()

    delay = random.uniform(base_min * multiplier, base_max * multiplier)
    await asyncio.sleep(delay)
    await random_pause()


async def batch_delay(batch_num: int, total_batches: int):
    if batch_num > 0 and batch_num % 5 == 0:
        pause = random.uniform(30, 60)
        logger.info(f"Batch {batch_num}/{total_batches} - taking break: {pause:.0f}s")
        await asyncio.sleep(pause)
    else:
        await asyncio.sleep(random.uniform(3, 8))