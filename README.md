# tg2obsidian

This program (hereinafter referred to as the Bot) utilizes the free functionality of the Telegram bot to save messages from a Telegram group into an [Obsidian](https://obsidian.md) vault on your local computer.

The Markdown formatting used will also work for most [other programs](https://www.markdownguide.org/tools/) that work with local Markdown files.
The Bot is designed to run locally on the computer where the Obsidian files are located.

This readme is also available [in Russian](README.ru.md).
## Use Case

- You write, dictate, or forward messages on the go to the Bot or to your personal Telegram group where the Bot is administrator
- The Bot receives new messages from Telegram and saves them as notes, thus forming an incoming stream of information directly into your note vault
- _Later, in a calm environment_, you process these notes, distributing the information from them to appropriate places in your vault

## Features

- One or more Teleram users could send messages to the Obsidian vault.
- Each user could use custom folder to store notes coming from Teleram.
- All messages are grouped by date — one note per day/month/year (according to the note name template) — or stored in a single note.
- Each message in a note has a header with a timestamp (can be suppressed for rapid message bursts).
- Depending on the settings, message formatting is either preserved or ignored.
- For forwarded messages, information about the message source is added.
- Photographs, animations, videos, and documents are saved in the vault and embedded in the note.
- Contacts are saved as YAML front matter and vcard.
- For locations, links to Google Maps and Yandex.Maps are created.
- There is an option to convert notes with specific keywords into tasks.
- There is an option to force all posts into tasks per chat via `/tasks on|off`.
- There is an option to tag notes with specific keywords.
- There is an option for OCR on images. In this case, the Bot sends the recognized text as a reply to the original message.
- There is an option for speech recognition from voice messages and audio messages (local Whisper or cloud OpenAI-compatible API). In this case, the Bot sends the recognized text as a reply to the original message.
- After processing a message, the bot adds OK emoji to it.

## Installation and Setup

The instructions below are intended for Windows users. For Linux and MacOS users, the installation and setup procedure is similar, but the commands for running programs may differ.

### Main Steps

1. Install [Python](https://python.org) 3.10+.
2. Install the required dependencies:

```shell
pip install -r requirements.txt
```

3. Create your bot using https://t.me/BotFather
4. Insert the token received from `@botfather` into the corresponding variable in the `config.py` file and modify the other parameters in `config.py` as required.
5. (Optional) Add the bot created above to a private Telegram group and make it an administrator so that it can read messages.
6. Run the bot (see the "Usage" section)
7. Send the `/start` command to your bot on Telegram. In response, the bot will tell you your id. Insert it into the `allowed_chats` parameter in the `config.py` file. Separate more than one chat id with a colon.

### Optional: Telegram Proxy

If direct access to Telegram is blocked in your network, the Bot can connect to the Telegram Bot API through a proxy.

Add the proxy settings to `config.py`:

```python
telegram_proxy_url = "socks5h://your-proxy-host:1080"
telegram_proxy_login = ""
telegram_proxy_password = ""
```

Notes:

- Leave `telegram_proxy_url` empty to keep using a direct connection.
- Supported proxy URL formats are `socks5h://...`, `socks5://...`, `socks4a://...`, `socks4://...`, and `http://...`.
- If your proxy requires authentication, fill `telegram_proxy_login` and `telegram_proxy_password`.
- The proxy is used only for Telegram Bot API requests and Telegram file downloads. Regular external URL previews are not routed through it.
- Proxy support requires the `aiohttp-socks` package, which is already included in `requirements.txt`.

#### Proxy / VPN how-tos

1. [How to set up full fledged VPN on VPS](https://github.com/ClusterM/vpn-how-to)
2. [How to set up SOCKS5 proxy on 3x-ui](SOCKS5-proxy-howto.md)

### If Text Recognition on Images is Required

1. Install [Tesseract](https://github.com/tesseract-ocr/tessdoc) and add the path to the executable file (tesseract.exe on Windows) to the system's PATH environment variable.
2. Navigate to the folder containing this script and ensure that tesseract.exe can be run from it.

### If Speech Recognition is Required

1. For local Whisper: install the compiled [FFMPEG](https://ffmpeg.org/download.html) and add the path to the executable file (ffmpeg.exe on Windows) to the system's PATH environment variable.
2. Navigate to the folder containing this script and ensure that ffmpeg.exe can be run from it.
3. For cloud STT: set `stt_provider = "cloud"` and fill `stt_base_url`, `stt_api_key`, `stt_model_name`, `stt_language` in `config.py` (OpenAI-compatible API).

## Usage

1. Send/forward messages that should be added to your Obsidian vault directly to your bot or to your private Telegram group.

2. Run the Bot:
```shell
python tg2obsidian_bot.py
```

- On a continuously running computer or server, the Bot can be left running. It will then recognize speech and add notes to Obsidian in real-time.
- If you only turn on your computer when you need to use it, run the Bot immediately when you need to receive messages in Obsidian, and close the program after receiving all messages.

**Important!** The Bot can only receive messages from the last 24 hours due to lifetime of [Telegram updates](https://core.telegram.org/bots/api#getting-updates). If more than 24 hours have passed since a message was sent before the Bot is run, that message will not be received by the Bot.

### Bot Commands

- `/start` — show chat id for `allowed_chats`.
- `/help` — show help.
- `/set_folder <path>` — set custom relative notes folder for the current chat.
- `/tasks on|off` — force all posts from this chat to be tasks (adds a task suffix).

### Timestamp Grouping

To avoid repeating timestamps for bursts of messages, set `message_timestamp_interval` in `config.py` (seconds). If a message arrives within this interval, the header timestamp is omitted for that message.
