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
    user_message = ''
    while True:
        line = await aioconsole.ainput('>')
        if line:
            user_message += line + '\n'
        else:
            print(user_message)
            logging.debug(f'sending: {user_message}')
            writer.write(f'{user_message}\n'.encode())
            await writer.drain()
            user_message = ''


async def register_name(reader, writer):
    line = await reader.readline()
    print(line.decode())
    nickname = await aioconsole.ainput('>')
    writer.write(f'{nickname}\n'.encode())
    await writer.drain()
    userdata = await reader.readline()
    return userdata


async def client_sender(userhash):
    address = 'minechat.dvmn.org'
    port = 5050
    reader, writer = await connect_to_chat(address, port, userhash)
    userdata = await reader.readline()
    if userdata == b'null\n':
        logging.error('Wrong user hash!')
        print('Wrong user hash! Check it or create new user.')
        userdata = await register_name(reader, writer)

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
    userhash = '3e92ea58-e903-11ee-aae7-0242ac110002!'
    asyncio.run(client_sender(userhash))

