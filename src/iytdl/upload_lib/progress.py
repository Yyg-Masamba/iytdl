__all__ = ["progress"]

import asyncio
import logging
import time

from math import floor
from typing import Dict, Tuple

from pyrogram import Client, ContinuePropagation, StopPropagation, StopTransmission
from pyrogram.errors import FloodWait, MessageNotModified

from iytdl.processes import Process
from iytdl.utils import *


_PROGRESS: Dict[str, Tuple[int, int]] = {}
LOG = logging.getLogger(__name__)


async def progress(
        current: int, 
        total: int, 
        client: Client, 
        process: Process, 
        filename: str, 
        mode: str = "upload", 
        edit_rate: int = 8, 
        total_file: dict = None
    ):
    """Pyrogram Upload / Download Progress Bar

    Parameters:
    ----------
        - current (`int`): The amount of bytes transmitted so far.
        - total (`int`): The total size of the file.
        - client (`Client`): Pyrogram Client.
        - process (`Process`): iytdl.process.Process.
        - filename (`str`): Display name of the file.
        - mode (`str`, optional): `"upload"` or `"download"`. (Defaults to `"upload"`)
        - edit_rate (`int`, optional): Message edit rate. (Defaults to `8`)
    """
    if process.is_cancelled:
        LOG.warning("Upload process is Cancelled")
        await client.stop_transmission()
    if total_file:
        x, y = total_file.get('now_video'), total_file.get('all_videos')
    else:
        x, y = 1, 1
    if x == y and current == total:
        if process.id not in _PROGRESS:
            return
        del _PROGRESS[process.id]
        try:
            await process.edit(f"`Finalizing {mode} process ...`")
        except FloodWait as f_w:
            await asyncio.sleep(f_w.value + 2)
        except MessageNotModified:
            pass
        return
    now = int(time.time())
    if process.id not in _PROGRESS:
        _PROGRESS[process.id] = now, now
    start, last_update_time = _PROGRESS[process.id]
    if now - last_update_time >= edit_rate:
        _PROGRESS[process.id] = start, now
        after = now - start
        speed = current / after
        eta = round((total - current) / speed)
        percentage = round(current / total * 100)
        progress_bar = f"[{'■' * floor(15 * percentage / 100)}{'□' * floor(15 * (1 - percentage / 100))}]"

        progress = f"""
<i>{mode.title()}ing:</i>  <code>{filename}</code>
<b>Completed:</b>  <code>{humanbytes(current)} / {humanbytes(total)}</code>
<b>Files:</b>  <code>[ {x} / {y} ]</code>
<b>Progress:</b>  <code>{progress_bar} {percentage} %</code>
<b>Speed:</b>  <code>{humanbytes(speed)}</code>
<b>ETA:</b>  <code>{time_formater(eta)}</code>
"""

        try:
            await process.edit(progress, reply_markup=process.cancel_markup)
        except FloodWait as f:
            await asyncio.sleep(f.value + 2)
        except (ContinuePropagation, MessageNotModified):
            pass
        except (StopPropagation, StopTransmission) as p_e:
            raise p_e
        except Exception:
            LOG.exception("Unable to Edit message")
