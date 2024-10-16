# tg2obsidian_bot - pulls posts from your private Telegram group
# and puts them in daily inbox note in your Obsidian vault
# Copyright (c) 2023-2024, Dmitry Ulanov
# https://github.com/dimonier/tg2obsidian

import os
import re
import logging
import aiohttp
import time
import asyncio
import aiofiles
import pytesseract

from pathlib import Path
from datetime import datetime as dt
from bs4 import BeautifulSoup
from pytz import timezone
import urllib.request

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Filter, Command
from aiogram.types import ContentType, File, Message, MessageEntity, Poll, PollAnswer
from aiogram.types.reaction_type_emoji import ReactionTypeEmoji
from aiogram.enums import ParseMode
from aiogram.methods.set_message_reaction import SetMessageReaction

import config

bot = Bot(token = config.token, parse_mode=ParseMode.HTML)
# router = Router()
dp = Dispatcher()

class Note:
    def __init__(self,
                 text = "",
                 date = dt.now().strftime('%Y-%m-%d'),
                 time = dt.now().strftime('%H:%M:%S')):
        self.text = text
        self.date = date
        self.time = time

basic_log = False
debug_log = False

if 'log_level' in dir(config) and config.log_level >= 1:
    basic_log = True
    if config.log_level >= 2:
        debug_log = True
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, filename = 'bot.log', encoding = 'UTF-8', datefmt = '%Y-%m-%d %H:%M:%S')
    log = logging.getLogger()

if config.recognize_voice:
    import torch
    import whisper
    import gc
    
    whisper_device = getattr(config, 'whisper_device', 'cpu')
    
    # Явно указываем torch использовать CPU
    if whisper_device == 'cpu':
        torch.cuda.is_available = lambda : False
    
    model = whisper.load_model(config.whisper_model)
    
    if whisper_device == 'cuda' and torch.cuda.is_available():
        model = model.to('cuda')
    else:
        model = model.to('cpu')

    print(f'Prepared for speech-to-text recognition on {whisper_device}')

# Handlers
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    log_basic(
        f"Starting chat with the user @{message.from_user.username} ({message.from_user.first_name} {message.from_user.last_name}, user_id = {message.from_user.id}), chat_id = {message.chat.id} ({message.chat.title})"
    )
    reply_text = f"Hello {message.from_user.full_name}!\n\nI`m a private bot, I save messages from a private Telegram group to Obsidian inbox.\n\nYour Id: {message.from_user.id}\nThis chat Id: {message.chat.id}\n"
    await message.reply(reply_text)

@dp.message(Command("help"))
async def help(message: types.Message):
    reply_text = '''/start - start Bot
    /help - show this help
    a text or picture message - to be passed into Obsidian inbox
    an audio message - to be recognized and passed into Obsidian inbox as text
    '''
    await message.reply(reply_text)

# @dp.message(F.voice)
async def handle_voice_message(message: Message):
    if message.chat.id != config.my_chat_id: return
    log_basic(f'Received (?) voice message from @{message.from_user.username}')
    log_message(message)
    if not config.recognize_voice:
        log_basic(f'Voice recognition is turned OFF')
        return
    note = note_from_message(message)
    voice = await bot.get_file(message.voice.file_id)
    path = os.path.dirname(__file__)

    await handle_file(file=voice, file_name=f"{voice.file_id}.ogg", path=path)
    file_full_path = os.path.join(path, voice.file_id + '.ogg')
    await bot.send_chat_action(chat_id=message.from_user.id, action=types.ChatActions.TYPING)

    try:
        note_stt = await stt(file_full_path)
        note.text = note_stt
    except Exception as e:
        await answer_message(message, f'🤷‍♂️ {e}')
    try:
        await answer_message(message, note_stt)
    except Exception as e:
        await answer_message(message, f'🤷‍♂️ {e}')
    save_message(note)
    os.remove(file_full_path)


# @dp.message_handler(content_types=[ContentType.AUDIO])
@dp.message(F.audio)
async def handle_audio(message: Message):
    if message.chat.id != config.my_chat_id: return
    log_basic(f'Received audio file from @{message.from_user.username}')
    log_message(message)
    if not config.recognize_voice:
        log_basic(f'Voice recognition is turned OFF')
        return
    note = note_from_message(message)
    try:
        audio = await message.audio.get_file()
    except Exception as e:
        log_basic(f'Exception: {e}')
        await answer_message(message, f'🤷‍♂️ {e}')
        return

    path = os.path.dirname(__file__)

    await handle_file(file=audio, file_name=f"{message.audio.file_name}", path=path)
    file_full_path = os.path.join(path, message.audio.file_name)
    await bot.send_chat_action(chat_id=message.from_user.id, action=types.ChatActions.TYPING)
    note_stt = await stt(file_full_path)
    try:
        await answer_message(message, note_stt)
    except Exception as e:
        await answer_message(message, f'🤷‍♂️ {e}')
    # Add label, if any, and a file name
    if message.caption != None:
        file_details = f'{bold(message.caption)} ({message.audio.file_name})'
    else:
        file_details = bold(message.audio.file_name)

    note.text = f'{file_details}\n{note_stt}'
    save_message(note)
    os.remove(file_full_path)


# @dp.message_handler(content_types=[ContentType.PHOTO])
@dp.message(F.photo)
async def handle_photo(message: Message):
    if message.chat.id != config.my_chat_id: return
    log_basic(f'Received photo from @{message.from_user.username}')
    log_message(message)
    note = note_from_message(message)
    photo = message.photo[-1]
    file_name = unique_indexed_filename(create_media_file_name(message, 'pic', 'jpg'), config.photo_path) # or photo.file_id + '.jpg'
    print(f'Got photo: {file_name}')
    photo_file = await bot.get_file(photo.file_id)

    await handle_file(file=photo_file, file_name=file_name, path=config.photo_path)

    forward_info = get_forward_info(message)
    photo_and_caption = f'{forward_info}![[{file_name}]]\n{await embed_formatting_caption(message)}'
    
    # Распознавание текста с фото
    try:
        from PIL import Image
        
        img = Image.open(os.path.join(config.photo_path, file_name))
        
        # # Попытка распознать русский текст
        # recognized_text_rus = pytesseract.image_to_string(img, lang='rus')
        # confidence_rus = pytesseract.image_to_data(img, lang='rus', output_type=pytesseract.Output.DICT)['conf']
        # avg_confidence_rus = sum(filter(lambda x: x != -1, confidence_rus)) / len(confidence_rus)
        
        # # Если уверенность низкая, попробуем распознать английский текст
        # if avg_confidence_rus < 50:
        #     recognized_text_eng = pytesseract.image_to_string(img, lang='eng')
        #     confidence_eng = pytesseract.image_to_data(img, lang='eng', output_type=pytesseract.Output.DICT)['conf']
        #     avg_confidence_eng = sum(filter(lambda x: x != -1, confidence_eng)) / len(confidence_eng)
            
        #     if avg_confidence_eng > avg_confidence_rus:
        #         recognized_text = recognized_text_eng
        #         # lang = "английский"
        #     else:
        #         recognized_text = recognized_text_rus
        #         # lang = "русский"
        # else:
        #     recognized_text = recognized_text_rus
        #     # lang = "русский"

        recognized_text = pytesseract.image_to_string(img, lang='rus+eng')

        if recognized_text.strip():
            photo_and_caption += f'\n\n{recognized_text}'
    except Exception as e:
        log_basic(f'Ошибка при распознавании текста: {e}')
    
    note.text = photo_and_caption
    save_message(note)

# @dp.message_handler(content_types=[ContentType.DOCUMENT])
@dp.message(F.document)
async def handle_document(message: Message):
    if message.chat.id != config.my_chat_id: return
    file_name = unique_filename(message.document.file_name, config.photo_path)
    log_basic(f'Received document {file_name} from @{message.from_user.username}')
    log_message(message)
    note = note_from_message(message)
    print(f'Got document: {file_name}')

    try:
        file = await bot.get_file(message.document.file_id)
        await handle_file(file=file, file_name=file_name, path=config.photo_path)
    except Exception as e:
        log_basic(f'Exception: {e}')
        await answer_message(message, f'🤷‍♂️ {e}')
        return

    if config.recognize_voice and message.document.mime_type.split('/')[0] == 'audio':
    # if mime type = "audio/*", recognize it like ContentType.AUDIO
        await bot.send_chat_action(chat_id=message.from_user.id, action=types.ChatActions.TYPING)

        file_full_path = os.path.join(config.photo_path, file_name)
        note_stt = await stt(file_full_path)
        try:
            await answer_message(message, note_stt)
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
        # Add label, if any, and a file name
        if message.caption != None:
            file_details = f'{bold(message.caption)} ({file_name})'
        else:
            file_details = bold(file_name)

        note.text = f'{file_details}\n{note_stt}'
        os.remove(file_full_path)
    else:
        forward_info = get_forward_info(message)
        note.text = f'{forward_info}[[{file_name}]]\n{await embed_formatting_caption(message)}'

    save_message(note)


# @dp.message_handler(content_types=[ContentType.CONTACT])
@dp.message(F.contact)
async def handle_contact(message: Message):
    if message.chat.id != config.my_chat_id: return
    log_basic(f'Received contact from @{message.from_user.username}')
    log_message(message)
    note = note_from_message(message)
    print(f'Got contact')
    note.text = await get_contact_data(message)
    save_message(note)


# @dp.message_handler(content_types=[ContentType.LOCATION])
@dp.message(F.location)
async def handle_location(message: Message):
    if message.chat.id != config.my_chat_id: return
    log_basic(f'Received location from @{message.from_user.username}')
    log_message(message)
    print(f'Got location')
    note = note_from_message(message)
    note.text = get_location_note(message)
    save_message(note)


# @dp.message_handler(content_types=[ContentType.ANIMATION])
@dp.message(F.animation)
async def handle_animation(message: Message):
    if message.chat.id != config.my_chat_id: return
    log_message(message)
    if message.document.file_name:
        file_name = unique_filename(message.document.file_name, config.photo_path)
    else:
        file_name = unique_indexed_filename(create_media_file_name(message, 'animation', 'mp4'), config.photo_path)
    log_basic(f'Received animation {file_name} from @{message.from_user.username}')
    print(f'Got animation: {file_name}')
    note = note_from_message(message)

    file = await bot.get_file(message.document.file_id)
#    file_path = file.file_path
    await handle_file(file=file, file_name=file_name, path=config.photo_path)

    forward_info = get_forward_info(message)
    note.text = f'{forward_info}![[{file_name}]]\n{await embed_formatting_caption(message)}'
    save_message(note)


# @dp.message_handler(content_types=[ContentType.VIDEO])
@dp.message(F.video)
async def handle_video(message: Message):
    if message.chat.id != config.my_chat_id: return
    log_message(message)
    if message.video.file_name:
        file_name = unique_filename(message.video.file_name, config.photo_path)
    else:
        file_name = unique_indexed_filename(create_media_file_name(message, 'video', 'mp4'), config.photo_path)
    log_basic(f'Received video {file_name} from @{message.from_user.username}')
    print(f'Got video: {file_name}')
    note = note_from_message(message)

    file = await bot.get_file(message.video.file_id)
#    file_path = file.file_path
    await handle_file(file=file, file_name=file_name, path=config.photo_path)

    note.text = f'{get_forward_info(message)}![[{file_name}]]\n{await embed_formatting_caption(message)}'
    save_message(note)


# @dp.message_handler(content_types=[ContentType.VIDEO_NOTE])
@dp.message(F.video_note)
async def handle_video_note(message: Message):
    if message.chat.id != config.my_chat_id: return
    log_message(message)
    file_name = unique_indexed_filename(create_media_file_name(message.video_note, 'video_note', 'mp4'), config.photo_path)
    log_basic(f'Received video note from @{message.from_user.username}')
    print(f'Got video note: {file_name}')
    note = note_from_message(message)

    file = await bot.get_file(message.video_note.file_id)
#    file_path = file.file_path
    await handle_file(file=file, file_name=file_name, path=config.photo_path)

    note.text = f'{get_forward_info(message)}![[{file_name}]]\n{await embed_formatting_caption(message)}'
    save_message(note)


# @dp.message_handler(content_types=[ContentType.POLL])
@dp.poll()
async def handle_poll(message: types.Poll):
    if message.chat.id != config.my_chat_id: return
    log_message(message)
    print(f'Got poll')

@dp.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    if message.chat.id != config.my_chat_id: return
    log_message(poll_answer)
    print(f'Got poll answer')

# @dp.message_handler()
@dp.message()
async def process_message(message: types.Message):
    if message.chat.id != config.my_chat_id: return
    log_basic(f'Received a message from @{message.from_user.username}')
    log_message(message)
    note = note_from_message(message)
    forward_info = get_forward_info(message)

    if message.photo:
        # processed above in another function, this code is never reached
        pass
    #     log_basic(f'Detected a photo')
    #     photo = message.photo[-1]
    #     file_name = unique_indexed_filename(create_media_file_name(message, 'pic', 'jpg'), config.photo_path) # or photo.file_id + '.jpg'
    #     print(f'Got photo: {file_name}')
    #     photo_file = await bot.get_file(photo.file_id)
    #     result = await handle_file(file=photo_file, file_name=file_name, path=config.photo_path)
    #     print(f'Success: {result}')

    #     photo_and_caption = f'{forward_info}![[{file_name}]]\n{await embed_formatting_caption(message)}'
    #     note.text=photo_and_caption

    elif message.sticker:
        log_basic(f'Detected a sticker')
        photo = message.sticker
        file_name = unique_indexed_filename(create_media_file_name(message, 'pic', 'webp'), config.photo_path) # or photo.file_id + '.jpg'
        print(f'Got sticker: {file_name}')
        photo_file = await bot.get_file(photo.file_id)
        result = await handle_file(file=photo_file, file_name=file_name, path=config.photo_path)
        print(f'Success: {result}')

        photo_and_caption = f'{forward_info}![[{file_name}]]\n{await embed_formatting_caption(message)}'
        note.text=photo_and_caption

    elif message.voice:
        log_basic(f'Detected voice message')
#        log_basic(f'Received audio file from @{message.from_user.username}')
#        log_message(message)
        if not config.recognize_voice:
            log_basic(f'Voice recognition is turned OFF')
            return
        note = note_from_message(message)

        path = os.path.dirname(__file__)
        voice_file = await bot.get_file(message.voice.file_id)
        voice_file_ext = message.voice.mime_type.split('/')[-1]
        file_name=f"{message.voice.file_id}.{voice_file_ext}"
        await handle_file(file=voice_file, file_name=file_name, path=path)

        file_full_path = os.path.join(path, file_name)
        await bot.send_chat_action(chat_id=message.from_user.id, action='typing')
        try:
            note_stt = await stt(file_full_path)
            note.text = note_stt
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
        try:
            await answer_message(message, note_stt)
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
        os.remove(file_full_path)

    elif message.video_note:
        log_basic(f'Detected video note')
        if not config.recognize_voice:
            log_basic(f'Voice recognition is turned OFF')
            return
        note = note_from_message(message)

        path = os.path.dirname(__file__)
        video_note_file = await bot.get_file(message.video_note.file_id)
        video_note_file_ext = '.mp4'
        file_name=f"{message.video_note.file_id}.{video_note_file_ext}"
        await handle_file(file=video_note_file, file_name=file_name, path=path)

        file_full_path = os.path.join(path, file_name)
        await bot.send_chat_action(chat_id=message.from_user.id, action='typing')
        try:
            note_stt = await stt(file_full_path)
            note.text = note_stt
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
        try:
            await answer_message(message, note_stt)
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
        os.remove(file_full_path)

    elif message.video:
        log_basic(f'Detected video')
        if not config.recognize_voice:
            log_basic(f'Voice recognition is turned OFF')
            return
        note = note_from_message(message)

        path = os.path.dirname(__file__)
        try:
            media_file = await bot.get_file(message.video.file_id)
#        media_file_ext = message.audio.mime_type.split('/')[-1]
            file_name= message.video.file_name
            await handle_file(file=media_file, file_name=file_name, path=path)
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
            note.text = f'{message.caption}\n' if message.caption else ""
            note.text += f'🤷‍♂️ {e}: {message.video.file_name} ({message.video.file_size} bytes)'
            save_message(note)
            return
        file_full_path = os.path.join(path, file_name)
        await bot.send_chat_action(chat_id=message.from_user.id, action='typing')
        try:
            note_stt = await stt(file_full_path)
            note.text = note_stt
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
        try:
            await answer_message(message, note_stt)
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
        os.remove(file_full_path)

    elif message.audio:
        log_basic(f'Detected audio message')
        if not config.recognize_voice:
            log_basic(f'Voice recognition is turned OFF')
            return
        note = note_from_message(message)

        path = os.path.dirname(__file__)
        try:
            media_file = await bot.get_file(message.audio.file_id)
#        media_file_ext = message.audio.mime_type.split('/')[-1]
            file_name= message.audio.file_name
            await handle_file(file=media_file, file_name=file_name, path=path)
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
            note.text = f'{message.audio.performer}\n' if message.audio.performer else ""
            note.text = f'{message.caption}\n' if message.caption else ""
            note.text += f'🤷‍♂️ {e}: {message.audio.file_name} ({message.audio.file_size} bytes)'
            save_message(note)
            return

        file_full_path = os.path.join(path, file_name)
        await bot.send_chat_action(chat_id=message.from_user.id, action='typing')

        note.text = f'{message.audio.performer}\n' if message.audio.performer else ""

        try:
            note_stt = await stt(file_full_path)
            note.text += note_stt
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
        try:
            await answer_message(message, note_stt)
        except Exception as e:
            await answer_message(message, f'🤷‍♂️ {e}')
        os.remove(file_full_path)

    elif message.poll:
        log_basic(f'Detected a poll')
        poll_options = ', '.join([option.text for option in message.poll.options])
        note.text = f"{message.poll.question} ({poll_options})"
    else:
        message_body = await embed_formatting(message)
        note.text = forward_info + message_body

    if message.link_preview_options:
        if message.link_preview_options.url and 'youtu' in message.link_preview_options.url:
            note.text += f'\n![{message.link_preview_options.url}]({message.link_preview_options.url})\n'

    save_message(note)
    await bot.set_message_reaction(chat_id=message.from_user.id, message_id=message.message_id, reaction=[{'type':'emoji', 'emoji':'👌'}])


# Functions

# Download the photo using aiohttp
async def handle_file(file: File, file_name: str, path: str):
    Path(f"{path}").mkdir(parents=True, exist_ok=True)
    destination = f"{path}/{file_name}"
#    await bot.download_file(file_path=file.file_path, destination=f"{path}/{file_name}")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.telegram.org/file/bot{config.token}/{file.file_path}") as resp:
            if resp.status == 200:
                f = await aiofiles.open(destination, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return (resp.status == 200)


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
        if m.forward_from.first_name:
            real_name += m.forward_from.first_name
        if m.forward_from.last_name:
            real_name += ' ' + m.forward_from.last_name
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
        result = bold(f'Forwarded {forward_info}') + '\n'
    else:
        result = ''

    return result

def log_message(message):
    # Saving of the whole message into the incoming message log just in case
    if debug_log:
        curr_date = dt.now().strftime('%Y-%m-%d')
        curr_time = dt.now().strftime('%H:%M:%S')
        file_name = 'messages-' + curr_date + '.txt'
        with open(file_name, 'a', encoding='UTF-8') as f:
            print(curr_time + '  ', list(message), '\n', file = f)
        log_debug(f'Message content saved to {file_name}')


def get_note_file_name_parts(curr_date):
    filename_part1 = config.note_prefix if 'note_prefix' in dir(config) else ''
    filename_part3 = config.note_postfix if 'note_postfix' in dir(config) else ''
    filename_part2 = curr_date if 'note_date' in dir(config) and config.note_date is True else ''
    return [filename_part1, filename_part2, filename_part3]

def get_note_name(curr_date) -> str:
    date_parts = curr_date.split('-')
    year, month, day = date_parts[0], date_parts[1], date_parts[2]
    
    note_name = config.note_name_template.format(year=year, month=month, day=day)
    return os.path.join(config.inbox_path, f'{note_name}.md')


def create_media_file_name(message: Message, suffix = 'media', ext = 'jpg') -> str:
    curr_date = get_curr_date()
    date_parts = curr_date.split('-')
    year, month, day = date_parts[0], date_parts[1], date_parts[2]
    
    note_name = config.note_name_template.format(year=year, month=month, day=day)
    
    # Remove unnecessary characters from the file name
    note_name = re.sub(r'[^\w\-_\.]', '_', note_name)
    
    return f'{curr_date}_{note_name}_{suffix}.{ext}'


def get_curr_date() -> str:
    return dt.now().strftime('%Y-%m-%d')


def one_line_note() -> bool:
    one_line_note = False if 'one_line_note' not in dir(config) or config.one_line_note == False else True
    return one_line_note


def format_messages() -> bool:
    format_messages = True if 'format_messages' not in dir(config) or config.format_messages else False
    return format_messages

def create_link_info() -> bool:
    return False if 'create_link_info' not in dir(config) else config.create_link_info

def save_message(note: Note) -> None:
    curr_date = note.date
    curr_time = note.time
    if one_line_note():
        # Replace all line breaks with spaces and make simple time stamp
        note_body = note.text.replace('\n', ' ')
        note_text = check_if_task(check_if_negative(f'[[{curr_date}]] - {note_body}\n'))
    else:
        # Keep line breaks and add a header with a time stamp
        note_body = check_if_task(check_if_negative(note.text))
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

# returns index of a first non ws character in a string
def content_index(c: str) -> int:
    ret = 0
    for i in c:
       if not i.isspace():
           return ret
       ret += 1
    return -1

# returns (ws?, content?, ws?)
def partition_string(text: str) -> tuple:
    start = content_index(text)
    if start == -1:
        return (text,'','')
    end = content_index(text[::-1])
    end = len(text) if end == -1 else len(text) - end
    return (text[:start], text[start:end], text[end:])

def to_u16(text: str) -> bytes:
    return text.encode('utf-16-le')

def from_u16(text: bytes) -> str:
    return text.decode('utf-16-le')


formats = {'bold': ('**', '**'),
           'italic': ('_', '_'),
           'underline': ('<u>', '</u>'),
           'strikethrough': ('~~', '~~'),
           'code': ('`', '`'),
}

def parse_entities(text: bytes,
    entities: list[MessageEntity],
    offset: int,
    end: int) -> str:
    formatted_note = ''

    for entity_index, entity in enumerate(entities):
        entity_start = entity['offset'] * 2
        if entity_start < offset:
            continue
        if entity_start > offset:
            formatted_note += from_u16(text[offset:entity_start])
        offset = entity_end = entity_start + entity['length'] * 2

        format = entity['type']
        if format == 'pre':
            pre_content = from_u16(text[entity_start:entity_end])
            content_parts = partition_string(pre_content)
            formatted_note += '```'
            if (len(content_parts[0]) == 0 and
                content_parts[1].find('\n') == -1):
                formatted_note += '\n'
            formatted_note += pre_content
            if content_parts[2].find('\n') == -1:
                formatted_note += '\n'
            formatted_note += '```'
            if (len(text) - entity_end < 2 or
               from_u16(text[entity_end:entity_end+2])[0] != '\n'):
                formatted_note += '\n'
            continue
        # parse nested entities for exampe: "**bold _italic_**
        sub_entities = [e for e in entities[entity_index + 1:] if e['offset'] * 2 < entity_end]
        parsed_entity = parse_entities(text, sub_entities, entity_start, entity_end)
        content_parts = partition_string(parsed_entity)
        content = content_parts[1]
        if format in formats:
            format_code = formats[format]
            formatted_note += content_parts[0]
            i = 0
            while i < len(content):
                index = content.find('\n\n', i) # inline formatting acros paragraphs, need to split
                if index == -1:
                    formatted_note += format_code[0] + content[i:] + format_code[1]
                    break
                formatted_note += format_code[0] + content[i:index] + format_code[1]
                i = index
                while i < len(content) and content[i] == '\n':
                    formatted_note += '\n'
                    i += 1
            formatted_note += content_parts[2]
            continue
        if format == 'mention':
            formatted_note += f'{content_parts[0]}[{content}](https://t.me/{content[1:]}){content_parts[2]}'
            continue
        if format == 'text_link':
            formatted_note += f'{content_parts[0]}[{content}]({entity["url"]}){content_parts[2]}'
            continue
        # Not processed (makes no sense): url, hashtag, cashtag, bot_command, email, phone_number
        # Not processed (hard to visualize using Markdown): spoiler, text_mention, custom_emoji
        formatted_note += parsed_entity

    if offset < end:
        formatted_note += from_u16(text[offset:end])
    return formatted_note

def is_single_url(message: Message) -> bool:
    # assuming there is atleast one entity
    entities = message.entities
    url_entity = entities[0]
    if url_entity['type'] == "url":
        return True
    if url_entity['type'] != "text_link":
        return False
    # need to check nested entities
    url_end = url_entity['offset'] + url_entity['length']
    for e in entities[1:]:
        if e['offset'] > url_end:
            return False
    return True

async def download(url, session: aiohttp.ClientSession) -> str:
    async with session.get(url) as response:
        return await response.text()

def get_open_graph_props(page: str) -> dict:
    props = {}
    soup = BeautifulSoup(page, 'lxml')
    meta = soup.find_all("meta", property=lambda x: x is not None and x.startswith("og:"))
    for m in meta:
        props[m['property'][3:].lstrip()] = m['content']
    if not 'description' in props:
        m = soup.find("meta", attrs={"name": "description"})
        if m:
            props['description'] = m['content']
    if not 'title' in props:
        props['title'] = soup.title.string

    return props

async def get_url_info_formatting(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        page = await download(url, session)
        og_props = get_open_graph_props(page)
        if 'image' in og_props or 'description' in og_props:
            sep = ''
            image = ''
            callout_type = "[!link-info-ni]"
            if 'image' in og_props:
                image += "!["
                if 'image:alt' in og_props:
                   image += og_props['image:alt'].replace("\n", " ")
                image += f"]({og_props['image']})"
                if 'image:width' in og_props and int(og_props['image:width']) < 600:
                    callout_type = "[!link-info]"
                else:
                    callout_type = "[!link-preview]"
                sep = "\n>"
            formatted_note = f'\n> {callout_type}'
            if 'site_name' in og_props:
                formatted_note += f" [{og_props['site_name']}]({url})"
            if 'title' in og_props:
                formatted_note += "\n> # " + og_props['title']
            if 'description' in og_props:
                formatted_note += "\n> "
                formatted_note += "\n> ".join(og_props['description'].split('\n')) + sep
            if 'image' in og_props:
                formatted_note += f"\n> [{image}]({url})"
            return formatted_note + "\n"
        return ''

async def embed_formatting(message: Message) -> str:
    # If the message contains any formatting (inclusing inline links), add corresponding Markdown markup
    note = message.text or ""

    if not format_messages():
        return note

    if not message.entities or len(message.entities) == 0:
        return note

    entities = message.entities
    formatted_note = ''
    try:
        note_u16 = to_u16(note)
        formatted_note = parse_entities(note_u16, entities, 0, len(note_u16))
        if create_link_info() and is_single_url(message):
            url_entity = entities[0]
            url = url_entity.get_text(note) if url_entity['type'] == "url" else url_entity['url']
            formatted_note += await get_url_info_formatting(url)
    except Exception as e:
        # If the message does not contain any formatting
        # await message.reply(f'🤷‍♂️ {e}')
        formatted_note = note
    return formatted_note


async def embed_formatting_caption(message: Message) -> str:
    # If the message contains any formatting (inclusing inline links), add corresponding Markdown markup
    note = message.caption or ""

    if not format_messages():
        return note

    if not message.caption_entities or len(message.caption_entities) == 0:
        return note

    entities = message.caption_entities
    formatted_note = ''
    try:
        note_u16 = to_u16(note)
        formatted_note = parse_entities(note_u16, entities, 0, len(note_u16))
        if create_link_info() and is_single_url(message):
            url_entity = entities[0]
            url = url_entity.get_text(note) if url_entity['type'] == "url" else url_entity['url']
            formatted_note += await get_url_info_formatting(url)
    except Exception as e:
        # If the message does not contain any formatting
        # await message.reply(f'🤷‍♂️ {e}')
        formatted_note = note
    return formatted_note

async def stt(audio_file_path) -> str:
    log_basic(f'Starting audio recognition on {whisper_device}')
    
    result = model.transcribe(audio_file_path, verbose=False, language='ru')
    
    if whisper_device == 'cuda' and torch.cuda.is_available():
        # Clear GPU memory
        torch.cuda.empty_cache()
    
    if hasattr(result['segments'], '__iter__'):
        rawtext = ' '.join([segment['text'].strip() for segment in result['segments']])
        rawtext = re.sub(" +", " ", rawtext)

        alltext = re.sub("([\.\!\?]) ", "\\1\n", rawtext)
        if debug_log:
            log_debug(f'Recognized: {alltext}')
        else:
            log_basic(f'Recognized {len(alltext)} characters')
    else:
        alltext = ""
        log_basic('Nothing recognized')

    return alltext

def unique_filename(file: str, path: str) -> str:
    """Change file name if file already exists"""
    # create target folder if not exist
    if not os.path.exists(path):
        os.makedirs(path)
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


def unique_indexed_filename(file: str, path: str) -> str:
    """Add minimal unique numeric index to file name to make up non existing file name"""
    # create target folder if not exist
    if not os.path.exists(path):
        os.makedirs(path)
    # get file name and extension
    filename, filext = os.path.splitext(file)
    # get full file path without extension only
    filexx = os.path.join(path, filename)
    # create incrementing variable
    i = 1
    # determine incremented filename
    while os.path.exists(f'{filexx}{i:02}{filext}'):
        # update the incrementing variable
        i += 1
    unique_indexed_filename = f'{filename}{i:02}{filext}'
    # create file to avoid reusing the same file name more than once
    with open(os.path.join(path, unique_indexed_filename), 'w') as f:
        f.write('')
    return unique_indexed_filename


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


async def answer_message(message: Message, answer_text: str):
    # Telegram limit is 4096 characters in a message
    msg_len_limit = 4000
    if len(answer_text) <= msg_len_limit:
        await message.answer(answer_text)
    else:
        chunks = text_to_chunks(answer_text, msg_len_limit)
        for chunk in chunks:
            try:
                await message.answer(chunk)
            except Exception as e:
                await message.answer(f'🤷‍♂️ {e}')
            time.sleep(0.03)


def text_to_chunks(text, max_len):
    """ Accepts a string text and splits it into parts of up to max_len characters. Returns a list of parts"""
    sentences = [piece.strip() + '.' for piece in text.split('.')]
    texts = []
    chunk = ''

    for sentence in sentences:
        if len(sentence) > max_len or len(chunk + ' ' + sentence) > max_len:
            # This sentence does not fit into the current chunk
            if len(chunk) > 0:
                # If there is something in the chunk, save it
                texts.append(chunk.strip(' '))
                chunk = ''
            # Chunk is empty, start filling it
            if len(sentence) > max_len:
                # If the current sentence is too long, put only as much as fits into the chunk
                words = sentence.split(' ')
                for word in words:
                    if len(chunk + ' ' + word) < max_len:
                        # This word fits into the current chunk, add it
                        chunk += ' ' + word
                    else:
                        # This word does not fit into the current chunk
                        texts.append(chunk.strip(' '))
                        chunk = word
            else:
                # Chunk was empty, so just add the sentence to it
                chunk = sentence

        else:
            # This sentence fits into the current chunk, add it
            chunk += ' ' + sentence
    # Save the last chunk, if it is not empty
    if len(chunk) > 0: texts.append(chunk.strip(' '))
    return texts

def get_location_note(message: Message) -> str:
    lat = message.location.latitude
    lon = message.location.longitude

    location_note = f'''{bold('Latitude')}: {lat}
{bold('Longitude')}: {lon}
[Google maps](https://www.google.com/maps/search/?api=1&query={lat},{lon}), [Yandex maps](https://yandex.ru/maps/?text={lat}%2C{lon}&z=17)
'''
    return location_note

def log_basic(text: str):
    if basic_log:
        log.info(text)


def log_debug(text: str):
    if debug_log:
        log.info(text)


def bold(text: str) -> str:
    if format_messages():
        return f'**{text}**'
    else:
        return text


def note_from_message(message: Message):
    local_tz = timezone(config.time_zone)
    message_date = message.date.astimezone(local_tz)
    msg_date = message_date.strftime('%Y-%m-%d')
    msg_time = message_date.strftime('%H:%M:%S')
    note = Note(date=msg_date, time=msg_time)
    return note


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
#    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
#dp = Dispatcher()
    # And the run events dispatching
    await dp.start_polling(bot)

if __name__ == '__main__':
    print('Bot started')
#    executor.start_polling(dp, skip_updates=False, relax = 1)
#    asyncio.get_event_loop().run_until_complete(main())
    asyncio.run(main())
# The code below never runs