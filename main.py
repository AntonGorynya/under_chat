import asyncio
import socket

import aiofiles
from environs import Env
import json
import gui
import logging
from anyio import create_task_group, run
from async_timeout import timeout
from client_reader import read_chat
from client_sender import connect_to_chat
from tkinter import messagebox, TclError
from os import path


logger = logging.getLogger('watchdog_logger')
logging.basicConfig(format='[%(created)f] %(message)s')
logger.setLevel(logging.DEBUG)

messages_queue = asyncio.Queue()
sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()
watchdog_queue = asyncio.Queue()


class InvalidToken(Exception):
    def __init__(self, userhash=None):
        self.msg = f'Invalid hash: «{userhash}»' if userhash else 'Empty hash'

    def __str__(self):
        return self.msg


def reconnect(reconnect_delay=3, state=None):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            while True:
                try:
                    return await func(*args, **kwargs)
                except (socket.gaierror, TimeoutError) as e:
                    logger.error(f'Lose connection! Error {type(e)}')
                    logger.debug(f'Waiting {reconnect_delay}s')
                    status_updates_queue.put_nowait(state)
                    await asyncio.sleep(reconnect_delay)
        return wrapper
    return decorator


@reconnect()
async def read_msgs(host='minechat.dvmn.org', port=5000, save_history=True, filepath='log.txt'):
    async with aiofiles.open(filepath, 'a') as file:
        async for message in read_chat(host, port, status_updates_queue, rise_exception=True):
            if save_history:
                await file.write(message)
            watchdog_queue.put_nowait('Connection is alive. New message in chat')
            await messages_queue.put(message.strip())


@reconnect(1, gui.SendingConnectionStateChanged.INITIATED)
async def send_msgs(user_hash, host='minechat.dvmn.org', port=5050):
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    reader, writer = await connect_to_chat(host, port, user_hash)
    watchdog_queue.put_nowait('Connection is alive. Prompt before auth')
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
    userdata = await reader.readline()
    userdata = json.loads(userdata.decode())
    if not userdata:
        raise InvalidToken(user_hash)
    watchdog_queue.put_nowait('Connection is alive. Authorization done')
    status_updates_queue.put_nowait(gui.NicknameReceived(userdata['nickname']))
    while True:
        try:
            msg = await asyncio.wait_for(sending_queue.get(), timeout=3)
        except asyncio.TimeoutError:
            msg = ''
            watchdog_queue.put_nowait('Sending empty message to the server')
        async with timeout(1):
            writer.write(f'{msg}\n\n'.encode())
            await writer.drain()
            await reader.readline()
        watchdog_queue.put_nowait('Connection is alive. Message sent')


async def watch_for_connection(delay=1, max_counter=3, dead_interval=2*5):
    attempt_counter = 0
    total_attempt_counter = 0
    while True:
        try:
            async with timeout(delay) as cm:
                msg = await watchdog_queue.get()
                if msg:
                    attempt_counter = 0
                    total_attempt_counter = 0
        except TimeoutError:
            logger.debug(f'{delay}s timeout is elapsed')
            attempt_counter += 1
            total_attempt_counter += 1
            if attempt_counter == max_counter:
                logger.debug(f'{max_counter} packets miss. Trying to reconnect...')
                attempt_counter = 0
            if total_attempt_counter*max_counter >= dead_interval:
                logger.debug(f'Server does not response for a long time')
                raise TimeoutError


async def handle_connection(host, snd_port, rcv_port, save_history, log_file, user_hash):
    try:
        async with create_task_group() as tg:
            tg.start_soon(gui.draw, messages_queue, sending_queue, status_updates_queue)
            tg.start_soon(watch_for_connection)
            tg.start_soon(read_msgs, host, rcv_port, save_history, log_file)
            tg.start_soon(send_msgs, user_hash, host, snd_port)
    except* InvalidToken as eg:
        msg = eg.exceptions[0]
        messagebox.showerror("Error", f"{msg}. Please check your configuration file")
    except* (gui.TkAppClosed, TimeoutError, TclError):
        print('Closing')


async def main() -> None:
    env = Env()
    env.read_env()

    host = env('HOST', 'minechat.dvmn.org')
    snd_port = env.int('SND_PORT', 5050)
    rcv_port = env.int('RCV_PORT', 5000)
    save_history = env.bool('SAVE_HISTORY')
    log_file = env('LOG_FILE')
    user_hash = env('USER_HASH')

    logger.debug('Program start')
    if path.exists(log_file):
        with open(log_file, 'r') as file:
            watchdog_queue.put_nowait('Reading history...')
            old_messages = file.readlines()
        for old_message in old_messages:
            await messages_queue.put(old_message.strip())
        watchdog_queue.put_nowait('History loaded')
    else:
        logger.debug(f'Log file {log_file} does not exist')
    await handle_connection(host, snd_port, rcv_port, save_history, log_file, user_hash)


if __name__ == '__main__':
    try:
        run(main)
    except KeyboardInterrupt:
        print('Closing!')
