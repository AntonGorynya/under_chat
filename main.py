import asyncio
import aiofiles
from environs import Env
import json
import gui
import logging
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


async def watch_for_connection(logging_level=logging.DEBUG):
    logger = logging.getLogger('watchdog_logger')
    logging.basicConfig(format='[%(created)f] %(message)s')
    logger.setLevel(logging_level)
    while True:
        msg = await watchdog_queue.get()
        logger.debug(msg)



async def main(host, snd_port, rcv_port, user_hash, save_history=False, log_file='log.txt'):
    # messages_queue = asyncio.Queue()
    # sending_queue = asyncio.Queue()
    # status_updates_queue = asyncio.Queue()
    # watchdog_queue = asyncio.Queue()

    watchdog_queue.put_nowait('Program start')
    with open(log_file, 'r') as file:
        watchdog_queue.put_nowait('Reading history...')
        old_messages = file.readlines()
    for old_message in old_messages:
        await messages_queue.put(old_message.strip())
    watchdog_queue.put_nowait('History loaded')

    # it is automatically scheduled as a Task.

    await asyncio.gather(
        read_msgs(host, rcv_port, save_history, log_file),
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        send_msgs(user_hash, host, port=snd_port),
        watch_for_connection(),
        return_exceptions=False
    )


if __name__ == '__main__':
    env = Env()
    env.read_env()

    host = env('HOST')
    snd_port = env.int('SND_PORT')
    rcv_port = env.int('RCV_PORT')
    save_history = env.bool('SAVE_HISTORY')
    log_file = env('LOG_FILE')
    user_hash = env('USER_HASH')

    loop = asyncio.new_event_loop()
    #loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(host, snd_port, rcv_port, user_hash, save_history=save_history, log_file=log_file))
    except InvalidToken as e:
        messagebox.showerror("Error", "Invalid Token. Please check your configuration file")
    except Exception as e:
        print(e)
    #asyncio.run(main(host, snd_port, rcv_port, user_hash, save_history=save_history, log_file=log_file))


