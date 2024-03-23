import aiofiles
import argparse
import asyncio
from datetime import datetime
import logging


async def read_chat(address, port):
    reader, writer = await asyncio.open_connection(address, port)
    try:
        data = b''
        while True:
            data += await reader.readline()
            if b'\n' in data:
                now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                message = f'[{now}] {data.decode()}'
                logging.debug(message)
                yield message
                data = b''
    except (ConnectionResetError, asyncio.exceptions.IncompleteReadError, UnicodeDecodeError):
        logging.error("Соединение разорвано.")
    finally:
        writer.close()
        await writer.wait_closed()


async def write_chat_log(adress, port, file_name='log_file.txt'):
    async with aiofiles.open(file_name, 'a') as file:
        async for message in read_chat(adress, port):
            if message is None:
                return 0
            await file.write(message)


def create_parser():
    parser = argparse.ArgumentParser(description='chat reader')
    parser.add_argument('--host', default='minechat.dvmn.org', help='IP or domain name')
    parser.add_argument('-p', '--port', default=5000, type=int, help='Port number')
    parser.add_argument('-v', '--verbose', action='store_true', help='Debug')
    parser.add_argument('--history', default='log_file.txt', type=str, help='History file name')
    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    try:
        asyncio.run(write_chat_log(args.host, args.port, file_name=args.history))
    except KeyboardInterrupt as e:
        logging.error("Прерывание с клавиатуры")
