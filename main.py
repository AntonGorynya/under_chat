import asyncio
import aiofiles
from environs import Env
import json
import gui
import logging
from anyio import create_task_group, run
from functools import wraps
from async_timeout import timeout
from client_reader import read_chat
from client_sender import connect_to_chat, send_message
from tkinter import messagebox


messages_queue = asyncio.Queue()
sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()
watchdog_queue = asyncio.Queue()


class InvalidToken(Exception):
    pass


async def read_msgs(host='minechat.dvmn.org', port=5000, save_history=True, filepath='log.txt'):
    async with aiofiles.open(filepath, 'a') as file:
        async for message in read_chat(host, port, status_updates_queue):
            if save_history:
                await file.write(message)
            watchdog_queue.put_nowait('Connection is alive. New message in chat')
            await messages_queue.put(message.strip())


async def send_msgs(user_hash, host='minechat.dvmn.org', port=5050):
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    watchdog_queue.put_nowait('Connection is alive. Prompt before auth')
    reader, writer = await connect_to_chat(host, port, user_hash)
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
    userdata = await reader.readline()
    userdata = json.loads(userdata.decode())
    if not userdata:
        raise InvalidToken
    watchdog_queue.put_nowait('Connection is alive. Authorization done')
    status_updates_queue.put_nowait(gui.NicknameReceived(userdata['nickname']))
    while True:
        msg = await sending_queue.get()
        writer.write(f'{msg}\n\n'.encode())
        await writer.drain()
        watchdog_queue.put_nowait('Connection is alive. Message sent')


async def watch_for_connection(logging_level=logging.DEBUG, delay=1):
    logger = logging.getLogger('watchdog_logger')
    logging.basicConfig(format='[%(created)f] %(message)s')
    logger.setLevel(logging_level)
    while True:
        try:
            async with timeout(delay) as cm:
                msg = await watchdog_queue.get()
                logger.debug(msg)
        except TimeoutError:
            logger.debug(f'{delay}s timeout is elapsed')
            raise ConnectionError


async def handle_connection(host, snd_port, rcv_port, save_history, log_file, user_hash):
    while True:
        try:
            print('Test')
            async with create_task_group() as tg:
                tg.start_soon(gui.draw, messages_queue, sending_queue, status_updates_queue)
                tg.start_soon(read_msgs, host, rcv_port, save_history, log_file)
                tg.start_soon(send_msgs, user_hash, host, snd_port)
                tg.start_soon(watch_for_connection)
        except* ConnectionError:
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)




async def main() -> None:
    env = Env()
    env.read_env()

    host = env('HOST')
    snd_port = env.int('SND_PORT')
    rcv_port = env.int('RCV_PORT')
    save_history = env.bool('SAVE_HISTORY')
    log_file = env('LOG_FILE')
    user_hash = env('USER_HASH')

    watchdog_queue.put_nowait('Program start')
    with open(log_file, 'r') as file:
        watchdog_queue.put_nowait('Reading history...')
        old_messages = file.readlines()
    for old_message in old_messages:
        await messages_queue.put(old_message.strip())
    watchdog_queue.put_nowait('History loaded')

    # async with create_task_group() as tg:
    #     tg.start_soon(gui.draw, messages_queue, sending_queue, status_updates_queue)
    #     tg.start_soon(watch_for_connection)
    #     tg.start_soon(read_msgs, host, rcv_port, save_history, log_file)
    #     tg.start_soon(send_msgs, user_hash, host, snd_port)
        #tg.start_soon(handle_connection)

    await handle_connection(host, snd_port, rcv_port, save_history, log_file, user_hash)


if __name__ == '__main__':
    #loop = asyncio.new_event_loop()
    try:
        #loop.run_until_complete(main())
        run(main)
    except InvalidToken as e:
        messagebox.showerror("Error", "Invalid Token. Please check your configuration file")
    except Exception as e:
        print(e)
