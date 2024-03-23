import asyncio
import aioconsole
import logging
import json


async def connect_to_chat(address, port, userhash=None):
    reader, writer = await asyncio.open_connection(address, port)
    data = await reader.readline()
    logging.debug(data)
    if userhash:
        logging.debug(f'User hash: {userhash}')
        userhash += '\n'
        writer.write(userhash.encode())
        await writer.drain()
    return reader, writer



async def send_message(writer):
    while True:

        print('ololo')
        writer.write('testmesage\n\n'.encode())
        await writer.drain()
        break


async def client_sender():
    address = 'minechat.dvmn.org'
    port = 5050
    userhash = '3e92ea58-e903-11ee-aae7-0242ac110002'
    reader, writer = await connect_to_chat(address, port, userhash)
    userdata = await reader.readline()
    userdata = json.loads(userdata.decode())
    username = userdata['nickname']
    print(f'Hello {username}! Post your message below. End it with an empty line.')
    try:
        await send_message(writer)
    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    asyncio.run(client_sender())

