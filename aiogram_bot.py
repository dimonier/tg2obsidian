import os
import re
# import logging
from pathlib import Path
# import asyncio
# import aioschedule as schedule
# import sqlite3
# import json
from datetime import datetime as dt

# import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
# from aiogram.contrib.fsm_storage.files import JSONStorage, MemoryStorage
# from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters import Text
# from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters.builtin import CommandStart, CommandHelp
from aiogram.types import ContentType, File, Message
from aiogram.utils import exceptions, executor
# from aiogram.utils import json as aijson

import config

########### Set constants

API_TOKEN = config.token

inbox_path = r'D:\Obsidian-Дима'
note_prefix = 'Telegram-'
task_keywords = {'задач', 'сделать', 'todo'}
negative_keywords = {'негатив'}

# Configure logging
# logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, filename = 'bot.log', encoding = 'UTF-8', datefmt = '%Y-%m-%d %H:%M:%S')
# log = logging.getLogger('broadcast')

bot = Bot(token = API_TOKEN)
dp = Dispatcher(bot)

# Handlers
@dp.message_handler(CommandStart())
async def send_welcome(message: types.Message):
    # logging.info(f'Starting chat with the user @{message.from_user.username} ({message.from_user.first_name} {message.from_user.last_name}, id = {message.from_id})')
    reply_text = f'Hello {message.from_user.full_name}!\nI`m a private bot who put messages from a private Telegram group to Obsidian inbox.\nYour Id: {message.from_id}!\n'
    await message.reply(reply_text)

@dp.message_handler(CommandHelp())
async def help(message: types.Message):
    reply_text = '''/start - start Bot
    /help - show this help
    a text message - to be passed into Obsidian inbox
    an audio message - to be recognized and passed into Obsidian inbox as text
    '''
    await message.reply(reply_text)

@dp.message_handler(content_types=[ContentType.VOICE])
async def voice_message_handler(message: Message):
    voice = await message.voice.get_file()
    path = r'D:\Work\Python\tg2obsidian'

    await handle_file(file=voice, file_name=f"{voice.file_id}.ogg", path=path)
    file_full_path = os.path.join(path, voice.file_id + '.ogg')
    note_stt = await stt(file_full_path)
    await message.answer(note_stt)
    await save_message(note_stt)
    os.remove(file_full_path)

@dp.message_handler()
async def process_message(message: types.Message):
    save_message(embed_formatting(message))
#    print(list(message))

# Functions
async def handle_file(file: File, file_name: str, path: str):
    Path(f"{path}").mkdir(parents=True, exist_ok=True)
    await bot.download_file(file_path=file.file_path, destination=f"{path}/{file_name}")

def save_message(note) -> None:
    curr_date = dt.now().strftime('%Y-%m-%d')
    curr_time = dt.now().strftime('%H:%M:%S')
    note_name = os.path.join(inbox_path, note_prefix + curr_date + '.md')
    note_body = check_if_task(check_if_negative(note))
    note_text = f'#### [[{curr_date}]] {curr_time}\n{note_body}\n\n'
    with open(note_name, 'a', encoding='UTF-8') as f:
        f.write(note_text)

def check_if_task(note_body) -> str:
    is_task = False
    for keyword in task_keywords:
        if keyword.lower() in note_body.lower(): is_task = True
    if is_task: note_body = '- [ ] ' + note_body
    return note_body

def check_if_negative(note_body) -> str:
    is_negative = False
    for keyword in negative_keywords:
        if keyword.lower() in note_body.lower(): is_negative = True
    if is_negative: note_body += '\n#негатив'
    return note_body

def embed_formatting(message) -> str:
    note = message['text']
    formats = {'bold': '**',
                'italic': '_',
                'underline': '==',
                'strikethrough': '~~',
                'spoiler': '',
                'code': '`',
    }
    formatted_note = ''
    tail = 0
    try:
        for entity in message['entities']:
            format = entity['type']
            start_pos = entity['offset']
            end_pos = start_pos + entity['length']
            # добавляем неформатированный кусок сообщения, если он есть
            if start_pos > tail:
                formatted_note += note[tail:start_pos]
                tail = start_pos
            # обрабатываем простые entity с симметричным форматированием
            if format in formats:
                format_code = formats[format]
                formatted_note += format_code + note[start_pos:end_pos] + format_code
            # обрабатываем сложные entity с несимметричным форматированием
            elif format == 'pre':
                formatted_note += '```\n' + note[start_pos:end_pos] + '\n```'
            elif format == 'mention':
                formatted_note += f'[{note[start_pos:end_pos]}](https://t.me/{note[start_pos+1:end_pos]})'
            elif format == 'text_link':
                formatted_note += f'[{note[start_pos:end_pos]}]({entity["url"]})'
            # Не сделано (нет смысла) для url, hashtag, cashtag, bot_command, email, phone_number
            # Не сделано (непонятно, как сделать) для spoiler, text_mention, custom_emoji
            else:
                formatted_note += note[start_pos:end_pos]
            tail = end_pos
#        print(list(message['entities']))
    except:
        formatted_note = note
    return formatted_note

async def stt(audio_file_path) -> str:
    import whisper
    model = whisper.load_model("medium")
    print('Audio recognition started')
    result = model.transcribe(audio_file_path, verbose = False, language = 'ru')
    rawtext = ' '.join([segment['text'].strip() for segment in result['segments']])
    rawtext = re.sub(" +", " ", rawtext)

    alltext = re.sub("([\.\!\?]) ", "\\1\n", rawtext)
    print('Recognized: ' + alltext)

    return alltext

#    return 'Boilerplate text'

##### Sending reminders

# async def remind():
#     print('reminder called')
#     broadcast_text = 'Остановись, осознай'
#     count = await broadcaster(broadcast_text)
#     logging.info(f'Sent reminder to {count} users')

# async def sched():
#     schedule.every().day.at("23:33").do(remind)
#     while True:
#         await schedule.run_pending()
#         await asyncio.sleep(5)
# #        print('cycling')

async def on_startup(__):
#     asyncio.create_task(sched())
    pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, relax = 1, on_startup=on_startup)
# То, что ниже, никогда не запускается
