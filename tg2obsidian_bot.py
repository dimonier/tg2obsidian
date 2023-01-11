# tg2obsidian_bot - pulls posts from your private Telegram group
# and puts them in daily inbox note in your Obsidian vault
# Copyright (c) 2023, Dmitry Ulanov
# https://github.com/dimonier/tg2obsidian

import os
import re
import logging
from pathlib import Path
from datetime import datetime as dt
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters.builtin import CommandStart, CommandHelp
from aiogram.types import ContentType, File, Message
from aiogram.utils import executor

import config

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, filename = 'bot.log', encoding = 'UTF-8', datefmt = '%Y-%m-%d %H:%M:%S')
log = logging.getLogger()

bot = Bot(token = config.token)
dp = Dispatcher(bot)

# Handlers
@dp.message_handler(CommandStart())
async def send_welcome(message: types.Message):
    log.info(f'Starting chat with the user @{message.from_user.username} ({message.from_user.first_name} {message.from_user.last_name}, user_id = {message.from_id}), chat_id = {message.chat.id} ({message.chat.title})')
    reply_text = f'Hello {message.from_user.full_name}!\n\nI`m a private bot, I save messages from a private Telegram group to Obsidian inbox.\n\nYour Id: {message.from_id}\nThis chat Id: {message.chat.id}\n'
    await message.reply(reply_text)

@dp.message_handler(CommandHelp())
async def help(message: types.Message):
    reply_text = '''/start - start Bot
    /help - show this help
    a text or picture message - to be passed into Obsidian inbox
    an audio message - to be recognized and passed into Obsidian inbox as text
    '''
    await message.reply(reply_text)

@dp.message_handler(content_types=[ContentType.VOICE])
async def handle_voice_message(message: Message):
#    if message.chat.id != config.my_chat_id: return
    log.info(f'Received voice message from @{message.from_user.username}')
    if not config.recognize_voice:
        log.info(f'Voice recognition is turned OFF')
        return
    voice = await message.voice.get_file()
    path = os.path.dirname(__file__)

    await handle_file(file=voice, file_name=f"{voice.file_id}.ogg", path=path)
    file_full_path = os.path.join(path, voice.file_id + '.ogg')
    note_stt = await stt(file_full_path)
    await message.answer(note_stt)
    save_message(note_stt)
    os.remove(file_full_path)

@dp.message_handler(content_types=[ContentType.PHOTO])
async def handle_photo(message: Message):
#    if message.chat.id != config.my_chat_id: return
    log.info(f'Received photo from @{message.from_user.username}')
    log_message(message)
    photo = message.photo[-1]
    file_name = unique_filename(create_photo_file_name(message), config.photo_path) # or photo.file_id + '.jpg'
    print(f'Got photo: {file_name}')
    photo_file = await photo.get_file()

    await handle_file(file=photo_file, file_name=file_name, path=config.photo_path)

    photo_message = {
        'text': message.caption,
        'entities': message.caption_entities,
        }
    forward_info = get_forward_info(message)
    photo_and_caption = f'{forward_info}![[{file_name}]]\n{embed_formatting(photo_message)}'
    save_message(photo_and_caption)

@dp.message_handler(content_types=[ContentType.DOCUMENT])
async def handle_document(message: Message):
#    if message.chat.id != config.my_chat_id: return
    file_name = unique_filename(message.document.file_name, config.photo_path)
    log.info(f'Received document {file_name} from @{message.from_user.username}')
    log_message(message)
    print(f'Got document: {file_name}')
    file = await message.document.get_file()
#    file_path = file.file_path
    await handle_file(file=file, file_name=file_name, path=config.photo_path)

    doc_message = {
        'text': message.caption,
        'entities': message.caption_entities,
        }

    forward_info = get_forward_info(message)
    doc_and_caption = f'{forward_info}[[{file_name}]]\n{embed_formatting(doc_message)}'
    save_message(doc_and_caption)


@dp.message_handler(content_types=[ContentType.CONTACT])
async def handle_contact(message: Message):
#    if message.chat.id != config.my_chat_id: return
    log.info(f'Received contact from @{message.from_user.username}')
    log_message(message)
    print(f'Got contact')
    contact_note = await get_contact_data(message)
    save_message(contact_note)


@dp.message_handler(content_types=[ContentType.LOCATION])
async def handle_location(message: Message):
#    if message.chat.id != config.my_chat_id: return
    log.info(f'Received location from @{message.from_user.username}')
    log_message(message)
    print(f'Got location')
    location_note = get_location_note(message)
    save_message(location_note)


@dp.message_handler(content_types=[ContentType.ANIMATION])
async def handle_animation(message: Message):
#    if message.chat.id != config.my_chat_id: return
    log.info(f'Received animation from @{message.from_user.username}')
    log_message(message)
    print(f'Got animation')


@dp.message_handler(content_types=[ContentType.VIDEO_NOTE])
async def handle_video_note(message: Message):
#    if message.chat.id != config.my_chat_id: return
    log.info(f'Received video note from @{message.from_user.username}')
    log_message(message)
    print(f'Got video note')


@dp.message_handler()
async def process_message(message: types.Message):
#    if message.chat.id != config.my_chat_id: return
    log.info(f'Received text message from @{message.from_user.username}')
    log_message(message)
    message_body = embed_formatting(message)
    forward_info = get_forward_info(message)
    save_message(forward_info + message_body)


# Functions
async def handle_file(file: File, file_name: str, path: str):
    Path(f"{path}").mkdir(parents=True, exist_ok=True)
    await bot.download_file(file_path=file.file_path, destination=f"{path}/{file_name}")

def get_forward_info(m: Message) -> str:
    # If the message is forwarded, extract forward info and make up forward header
    forward_info = ''
    post = 'message'
    user = ''
    chat = ''
    forwarded = False
    if m.forward_from_chat:
        forwarded = True
        # Todo: unversal parser of chat id. Currently works for sure for channels only
        chat_id = str(m.forward_from_chat.id)[4:]
        if m.forward_from_chat.username:
            chat_name = f'[{m.forward_from_chat.title}](https://t.me/{m.forward_from_chat.username})'
        else:
            chat_name = f'{m.forward_from_chat.title}'
        chat = f'from {m.forward_from_chat.type} {chat_name}'

        if m.forward_from_message_id:
            msg_id = str(m.forward_from_message_id)
            post = f'[message](https://t.me/c/{chat_id}/{msg_id})'

    if m.forward_from:
        forwarded = True
        real_name = ''
        if 'first_name' in m.forward_from: real_name += m.forward_from.first_name
        if 'last_name' in m.forward_from: real_name += ' ' + m.forward_from.last_name
        real_name = real_name.strip()
        if m.forward_from.username:
            user = f'by [{real_name}](https://t.me/{m.forward_from.username})'
        else:
            user = f'by {real_name}'
    elif m.forward_sender_name:
        forwarded = True
        user = f'by {m.forward_sender_name}'

    forward_info = ' '.join([item for item in [post, chat, user] if len(item) > 0])

    if forwarded:
        result = f'**Forwarded {forward_info}**\n'
    else:
        result = ''

    return result

def log_message(message):
    # Saving of the whole message into the incoming message log just in case
    curr_date = dt.now().strftime('%Y-%m-%d')
    curr_time = dt.now().strftime('%H:%M:%S')
    file_name = 'messages-' + curr_date + '.txt'
    with open(file_name, 'a', encoding='UTF-8') as f:
        print(curr_time + '  ', list(message), '\n', file = f)
    log.info(f'Message content saved to {file_name}')


def get_note_file_name_parts(curr_date):
    filename_part1 = config.note_prefix if 'note_prefix' in dir(config) else ''
    filename_part3 = config.note_postfix if 'note_postfix' in dir(config) else ''
    filename_part2 = curr_date if 'note_date' in dir(config) and config.note_date is True else ''
    return [filename_part1, filename_part2, filename_part3]

def get_note_name(curr_date) -> str:
    parts = get_note_file_name_parts(curr_date)
    return os.path.join(config.inbox_path, ''.join(parts) + '.md')


def create_photo_file_name(message: Message) -> str:
    # ToDo: переделать на дату отправки сообщения
    curr_date = get_curr_date()
    parts = get_note_file_name_parts(curr_date)
    # ToDo: добавить в имя файлаusername исходного канала или пользователя
    # Если присутствует forward_from - оттуда, иначе из from

    # Строим среднюю часть имени без лишних - и _
    note_name = re.sub("[-_]+", "-", f'{parts[0]}{parts[2]}'.strip('-_'))

    return f'{curr_date}_{note_name}_pic.jpg'


def get_curr_date() -> str:
    return dt.now().strftime('%Y-%m-%d')


def save_message(note: str) -> None:
    curr_date = dt.now().strftime('%Y-%m-%d')
    curr_time = dt.now().strftime('%H:%M:%S')
    note_body = check_if_task(check_if_negative(note))
    note_text = f'#### [[{curr_date}]] {curr_time}\n{note_body}\n\n'
    with open(get_note_name(curr_date), 'a', encoding='UTF-8') as f:
        f.write(note_text)

def check_if_task(note_body) -> str:
    is_task = False
    for keyword in config.task_keywords:
        if keyword.lower() in note_body.lower(): is_task = True
    if is_task: note_body = '- [ ] ' + note_body
    return note_body

def check_if_negative(note_body) -> str:
    is_negative = False
    for keyword in config.negative_keywords:
        if keyword.lower() in note_body.lower(): is_negative = True
    if is_negative: note_body += f'\n{config.negative_tag}'
    return note_body

def embed_formatting(message) -> str:
    # If the message contains any formatting (inclusing inline links), add corresponding Markdown markup
    note = message['text']

    if not config.format_messages:
        return note

    formats = {'bold': '**',
                'italic': '_',
                'underline': '==',
                'strikethrough': '~~',
                'code': '`',
    }
    formatted_note = ''
    tail = 0
    try:
        if len(message['entities']) == 0: formatted_note = note
        for entity in message['entities']:
            format = entity['type']
            start_pos = entity['offset']
            end_pos = start_pos + entity['length']
            # Add unformatted piece of text before this entity, if exists
            if start_pos > tail:
                formatted_note += note[tail:start_pos]
                tail = start_pos
            # Process simple entities with symmetrical markup
            if format in formats:
                format_code = formats[format]
                formatted_note += format_code + note[start_pos:end_pos].strip() + format_code
                # Restore space after formatted text if it was placed before the closing markup
                if note[end_pos-1] == ' ': formatted_note += ' '
            # Process complex entities having asymmetrical markup
            elif format == 'pre':
                formatted_note += '```\n' + note[start_pos:end_pos] + '\n```'
            elif format == 'mention':
                formatted_note += f'[{note[start_pos:end_pos]}](https://t.me/{note[start_pos+1:end_pos]})'
            elif format == 'text_link':
                formatted_note += f'[{note[start_pos:end_pos]}]({entity["url"]})'
            # Not processed (makes no sense): url, hashtag, cashtag, bot_command, email, phone_number
            # Not processed (hard to visualize using Markdown): spoiler, text_mention, custom_emoji
            else:
                formatted_note += note[start_pos:end_pos]
            tail = end_pos
        # Add unformatted trailing piece of text, if exists
        if len(message['entities']) > 0 and tail < len(note):
            formatted_note += note[tail:]
    except:
        # If the message does not contain any formatting
        formatted_note = note
    return formatted_note

async def stt(audio_file_path) -> str:
    import whisper
    model = config.whisper_model if 'whisper_model' in dir(config) else 'medium'
    model = whisper.load_model(model)

    log.info('Audio recognition started')
    result = model.transcribe(audio_file_path, verbose = False, language = 'ru')
    rawtext = ' '.join([segment['text'].strip() for segment in result['segments']])
    rawtext = re.sub(" +", " ", rawtext)

    alltext = re.sub("([\.\!\?]) ", "\\1\n", rawtext)
    log.info(f'Recognized: {alltext}')

    return alltext

def unique_filename(file: str, path: str) -> str:
    """Change file name if file already exists"""
    # check if file exists
    if not os.path.exists(os.path.join(path, file)):
        return file
    # get file name and extension
    filename, filext = os.path.splitext(file)
    # get full file path without extension only
    filexx = os.path.join(path, filename)
    # create incrementing variable
    i = 1
    # determine incremented filename
    while os.path.exists(f'{filexx}_{str(i)}{filext}'):
        # update the incrementing variable
        i += 1
    return f'{filename}_{str(i)}{filext}'


async def get_contact_data(message: Message) -> str:

    if message.contact.user_id:
        contact_user  = await get_telegram_username(message.contact.user_id)

    frontmatter_body = ''
    for field, value in message.contact:
        if field not in ('vcard', 'user_id'):
            frontmatter_body += f'{field}: {value}\n'

    note_frontmatter = f'''<!-- YAML front matter -->

---
{frontmatter_body}
---
'''

    fname = message.contact.first_name or ''
    lname = message.contact.last_name or ''
    contact_name = f'{fname} {lname}'.strip()

    note_body = f'''<!-- vcard -->
[[{contact_name}]]
Telegram: {contact_user}
```vcard
{message.contact.vcard}
```
'''

    return note_frontmatter + note_body


async def get_telegram_username(user_id: int) -> str:
    user_info = await bot.get_chat_member(user_id, user_id)
    if 'username' in user_info.user:
        result = f'[@{user_info.user.username}](https://t.me/{user_info.user.username})'
    else:
        fname = user_info.user.first_name or ''
        lname = user_info.user.last_name or ''
        result = f'{fname} {lname}'.strip()

    return result


def get_location_note(message: Message) -> str:
    lat = message.location.latitude
    lon = message.location.longitude

    location_note = f'''**Latitude**: {lat}
**Longitude**: {lon}
[Google maps](https://www.google.com/maps/search/?api=1&query={lat},{lon}), [Yandex maps](https://yandex.ru/maps/?text={lat}%2C{lon}&z=17)
'''
    return location_note


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, relax = 1)

# The code below never runs
