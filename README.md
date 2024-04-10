# under_chat
<img width="494" alt="image" src="https://github.com/AntonGorynya/under_chat/assets/15812508/46d03602-dcae-4e99-9165-86f9d949da2a">

Репозитарий представляет собой 4 скрипта.
 - `client_reader.py` читает сообщения с сервера. И записывает их в файл. По умолчанию `log.txt`
 - `client_sender.py` позволяет отправлять сообщения. А так же регистрироваться на сервере через консоль
 - `gui_registration.py` Графическая форма регистрации
 - `main.py` Графический чат клиент

## Установка
Python 3.9 должен быть установлен.

```commandline
python -m pip install -r requirements.txt
```

## Запуск 
```commandline
> python.exe .\client_sender.py
Connect ot the server minechat.dvmn.org:5050
User hash not found! Run program with hash or register new user.
Enter preferred nickname below:

>Nickname
Hello Goofy Nickname! Post your message below. End it with an empty line.
>test message
>
```

