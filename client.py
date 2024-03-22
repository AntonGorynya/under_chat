import asyncio


async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        'minechat.dvmn.org', 5000)
    data = b''
    while True:
        data += await reader.read(100)
        if b'\n' in data:
            print(f'decode: {data.decode()}')
            data = b''



if __name__ == '__main__':
    asyncio.run(tcp_echo_client('Hello World!'))