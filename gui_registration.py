import asyncio
import json
from tkinter import *
from environs import Env
from anyio import create_task_group, run
from gui import update_tk, TkAppClosed
from socket import gaierror


async def register(host, port, username_entry, info_label):
    username = username_entry.get()
    while True:
        try:
            msg = 'Введити никнейм'
            if username:
                reader, writer = await asyncio.open_connection(host, port)
                await reader.readline()
                writer.write(b'\n')
                await writer.drain()
                await reader.readline()
                writer.write(f'{username}\n'.encode())
                await writer.drain()
                userdata = await reader.readline()
                userdata = json.loads(userdata.decode())
                account_hash = userdata['account_hash']
                with open('.env', 'w+') as file:
                    rows = file.readlines()
                    rows = [row for row in rows if 'USER_HASH' not in rows]
                    rows.append(f'USER_HASH={account_hash}')
                    file.writelines(rows)
                msg = f'Вы успешно зарегестрированы!'
            info_label['text'] = msg
            return 0
        except (TimeoutError, gaierror):
            info_label['text'] = 'Отсутсвует подключение к интернету'
            return -1




async def draw(host, port):
    root = Tk()
    root.title('Registration form')
    root.geometry('250x200')
    root_frame = Frame()

    agenda = Label(root, text='Добро пожаловать в чат по Minecraft.\n Заполните форму регистрации ниже')
    username_entry = Entry(root, width=120)
    info_label = Label(root, width=120)
    registration_button = Button(
        root,
        text='Зарегистрироваться',
        command=lambda: asyncio.create_task(register(host, port, username_entry, info_label))
    )
    agenda.pack()
    username_entry.pack()
    registration_button.pack()
    info_label.pack()

    async with create_task_group() as tg:
        tg.start_soon(update_tk, root_frame)
    root.destroy()


async def main():
    env = Env()
    env.read_env()
    host = env('HOST', 'minechat.dvmn.org')
    port = env.int('SND_PORT', 5050)

    async with create_task_group() as tg:
        tg.start_soon(draw, host, port)


if __name__ == '__main__':
    try:
        run(main)
    except* (KeyboardInterrupt, TkAppClosed):
        print('Exiting')
