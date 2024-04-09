import asyncio
from tkinter import *
from environs import Env
from anyio import create_task_group, run


async def register(host, port, username_entry, info_label):
    username = username_entry.get()
    if username:
        reader, writer = asyncio.open_connection(host, port)
        info_label['text'] = f'Жмяк'
    else:
        info_label['text'] = f'Введити никнейм'


async def draw(host, port):
    root = Tk()
    root.title('Registration form')
    root.geometry('250x200')

    agenda = Label(root, text='Добро пожаловать в чат по Minecraft.\n Заполните форму регистрации ниже')
    username_entry = Entry(root, width=120)
    registration_button = Button(
        root,
        text="Зарегистрироваться",
        command=lambda: register(host, port, username_entry, info_label)
    )
    info_label = Label(root, width=120)

    agenda.pack()
    username_entry.pack()
    registration_button.pack()
    info_label.pack()
    await root.mainloop()



async  def main():
    env = Env()
    env.read_env()
    host = env('HOST', 'minechat.dvmn.org')
    port = env.int('SND_PORT', 5050)

    async with create_task_group() as tg:
        tg.start_soon(draw, host, port)


if __name__ == '__main__':
    #run(main)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())