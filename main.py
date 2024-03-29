import asyncio
import aiofiles
from environs import Env
import json
import gui
import logging
from client_reader import read_chat
from client_sender import connect_to_chat, send_message
from tkinter import messagebox


class InvalidToken(Exception):
    pass


async def read_msgs(
        messages_queue, host='minechat.dvmn.org', port=5000, save_history=True, filepath='log.txt'):
    async with aiofiles.open(filepath, 'a') as file:
        async for message in read_chat(host, port):
            if save_history:
                await file.write(message)
            await messages_queue.put(message.strip())


async def send_msgs(queue, user_hash, host='minechat.dvmn.org', port=5050):
    reader, writer = await connect_to_chat(host, port, user_hash)
    userdata = await reader.readline()
    userdata = json.loads(userdata.decode())
    if not userdata:
        raise InvalidToken
    logging.debug(userdata)
    while True:
        msg = await queue.get()
        logging.debug(msg)
        writer.write(f'{msg}\n\n'.encode())
        await writer.drain()


async def main(host, snd_port, rcv_port,user_hash, save_history=False, log_file='log.txt'):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    with open(log_file, 'r') as file:
        old_messages = file.readlines()
    for old_message in old_messages:
        await messages_queue.put(old_message.strip())

    # it is automatically scheduled as a Task.

    await asyncio.gather(
        read_msgs(messages_queue, host, rcv_port, save_history, log_file),
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        send_msgs(sending_queue, user_hash, host, port=snd_port),
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

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(host, snd_port, rcv_port, user_hash, save_history=save_history, log_file=log_file))
    except InvalidToken as e:
        messagebox.showerror("Error", "Invalid Token. Please check your configuration file")
    #asyncio.run(main(host, snd_port, rcv_port, user_hash, save_history=save_history, log_file=log_file))


