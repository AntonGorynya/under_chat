import asyncio
import aioconsole
import logging
import json


async def connect_to_chat(address, port, userhash=None):
    reader, writer = await asyncio.open_connection(address, port)
    data = await reader.readline()
    logging.debug(f'connect to the server')
    if userhash:
        logging.debug(f'User hash: {userhash}')
        userhash += '\n'
        writer.write(userhash.encode())
        await writer.drain()
    else:
        logging.debug(f'User hash not found')
        print(data.decode())
        line = await aioconsole.ainput('>')
        print(line)
        if not line:
            writer.write(b'\n')
            await writer.drain()
    return reader, writer


async def send_message(writer):
    user_message = ''
    while True:
        line = await aioconsole.ainput('>')
        if line:
            user_message += line + '\n'
        else:
            user_message = user_message.replace('\n', ' ')
            logging.debug(f'sending: {user_message}')
            writer.write(f'{user_message}\n'.encode())
            await writer.drain()
            user_message = ''


async def register_name(reader, writer, save_to_file=True):
    line = await reader.readline()
    print(line.decode())
    nickname = await aioconsole.ainput('>')
    writer.write(f'{nickname}\n'.encode())
    await writer.drain()
    userdata = await reader.readline()
    userdata = json.loads(userdata.decode())
    logging.debug(f'new user data: {userdata}')
    if save_to_file:
        with open('credential.json', 'w') as file:
            json.dump(userdata, file)
            logging.debug('credentials are saved')
    return userdata


async def client_sender(userhash):
    address = 'minechat.dvmn.org'
    port = 5050
    reader, writer = await connect_to_chat(address, port, userhash)
    if userhash:
        logging.debug(f'User hash is {userhash}')
        userdata = await reader.readline()
        userdata = json.loads(userdata.decode())
    else:
        logging.debug('No user hash. Creat new user')
        userdata = await register_name(reader, writer)
    if userdata is None:
        logging.error('Wrong user hash!')
        print('Wrong user hash! Check it or create new user.')
        userdata = await register_name(reader, writer)

    username = userdata['nickname']
    print(f'Hello {username}! Post your message below. End it with an empty line.')
    try:
        await send_message(writer)
    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    userhash = '3e92ea58-e903-11ee-aae7-0242ac110002'
    #userhash = ''
    asyncio.run(client_sender(userhash))

