import asyncio
from datetime import datetime
import aiofiles
import logging


async def read_chat(adress, port):
    try:
        reader, writer = await asyncio.open_connection(adress, port)
        data = b''
        while True:
            data += await reader.read(100)
            if b'\n' in data:
                now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                message = f'[{now}] {data.decode()}'
                logging.debug(message)
                yield message
                data = b''
    except (ConnectionResetError, asyncio.exceptions.IncompleteReadError):
        logging.error("Соединение разорвано.")
    finally:
        writer.close()
        await writer.wait_closed()
        yield None

async def write_chat_log(adress, port, file_name='log_file.txt'):
    async with aiofiles.open(file_name, 'a') as file:
        async for message in read_chat(adress, port):
            await file.write(message)



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #asyncio.run(read_chat('minechat.dvmn.org', 5000, log=True))
    try:
        asyncio.run(write_chat_log('minechat.dvmn.org', 5000))
    except Exception as e:
        print(e)
