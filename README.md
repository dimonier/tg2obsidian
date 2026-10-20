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

## Installation and First Run

Install [Python](https://python.org) 3.10–3.14 and download the project. A [detailed Windows guide with screenshots](extended_tg2obsidian_manual.ru.md) is available in Russian.

Start by setting up ordinary text messages. You can add text and speech recognition later using the instructions below.

### 1. Install the Required Packages

Open a terminal in the project folder. On Windows, use **Command Prompt (cmd)** rather than PowerShell: the commands below are written for cmd.

Create a separate environment for the bot so its packages do not interfere with other programs:

```shell
python -m venv .venv
```

Activate the environment on Windows:

```bat
.venv\Scripts\activate.bat
```

Or on Linux/macOS:

```shell
source .venv/bin/activate
```

Install the packages:

```shell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Activate this environment again whenever you open a new terminal. Use it both to install optional packages and to run the bot. Double-clicking `tg2obsidian_bot.bat` does not activate the environment.

### 2. Create and Configure the Bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram, send `/newbot`, and follow its instructions.
2. Copy the token into the `token` setting in `config.py`. Do not publish this token or include it in commits.
3. In the same file, set the paths to folders in your Obsidian vault:

   - `inbox_path` — where notes are written;
   - `photo_path` — where attachments are saved.

   Create these folders if they do not exist. This Windows example uses placeholder paths; replace them with your own:

   ```python
   inbox_path = r'C:\Users\you\Documents\MyVault\Telegram'
   photo_path = r'C:\Users\you\Documents\MyVault\attachments'
   ```

   On Linux or macOS, use your own full paths, such as `/home/you/MyVault/Telegram`.

### 3. Allow Messages From Your Chat

Start the bot in the same terminal:

```shell
python tg2obsidian_bot.py
```

Open your bot in Telegram and send `/start`. Until the chat is allowed, the bot replies with a message containing the chat's numeric ID.

Stop the bot with `Ctrl+C`, put that ID in `config.py`, and save the file:

```python
allowed_chats = '123456789'
```

Run `python tg2obsidian_bot.py` again and send a plain text message. It should appear in a note in `inbox_path`.

To allow several chats, separate their IDs with colons: `'123456789:987654321'`. Restart the bot after changing its settings.

## Optional Features

### Messages From a Group

Add the bot to a private group and make it an administrator so it can read messages. Send `/start` in the group, add its ID to `allowed_chats`, and restart the bot. Open a private conversation with the bot first, as described above.

### Connecting Through a Proxy

If a direct connection to Telegram is unavailable, configure a proxy in `config.py`:

```python
telegram_proxy_url = "socks5h://your-proxy-host:1080"
telegram_proxy_login = ""
telegram_proxy_password = ""
```

- Leave `telegram_proxy_url` empty for a direct connection.
- Supported schemes are `socks5h://`, `socks5://`, `socks4a://`, `socks4://`, and `http://`.
- If credentials are required, fill `telegram_proxy_login` and `telegram_proxy_password`.
- The proxy is used for Telegram connections and attachment downloads. External link previews do not use it.
- The required packages are already included in the basic installation.

Proxy / VPN setup guides:

1. [How to set up full fledged VPN on VPS](https://github.com/ClusterM/vpn-how-to)
2. [How to set up SOCKS5 proxy on 3x-ui](SOCKS5-proxy-howto.md)

### Recognizing Text in Images

In the activated environment, run:

```shell
python -m pip install -r requirements-ocr.txt
```

Install [Tesseract](https://github.com/tesseract-ocr/tessdoc) with the required language data, and add its executable directory to PATH. The command `tesseract --version` should print its version.

Set `ocr = True`, configure `ocr_languages` in `config.py`, and restart the bot.

### Transcribing Speech

Voice messages and audio messages are skipped by default. To turn them into text, choose one of the two recognition methods below. Audio files sent as documents are saved as regular attachments.

#### On Your Computer, With Whisper

In the activated environment, run:

```shell
python -m pip install -r requirements-voice-local.txt
```

Install [FFmpeg](https://ffmpeg.org/download.html) and add its executable directory to PATH. Check it with `ffmpeg -version`.

In `config.py`, set:

```python
recognize_voice = True
stt_provider = "local"
```

Restart the bot. On the first run, it downloads the model selected in `whisper_model`. Torch and the model can use substantial disk space and memory.

Whisper and Torch may not support every Python version. Check the requirements of [Whisper](https://github.com/openai/whisper#setup) and [PyTorch](https://pytorch.org/get-started/locally/) before installing them. For GPU use, follow the Torch installation instructions on the PyTorch website.

#### Through a Cloud Service

In the activated environment, run:

```shell
python -m pip install -r requirements-voice-cloud.txt
```

Set `recognize_voice = True` and `stt_provider = "cloud"` in `config.py`. Fill in the service address `stt_base_url`, API key `stt_api_key`, model name `stt_model_name`, and language `stt_language`, then restart the bot. The service must provide an OpenAI-compatible API.

Audio is sent to the selected provider. This method does not require Whisper, Torch, or FFmpeg.

Install recognition packages only if you need them. Each `requirements-*.txt` file also includes the basic bot dependencies; you can install more than one.

## If the Bot Does Not Start

Open a terminal in the project folder, activate the environment, and run:

```shell
python -m pip check
python -m unittest discover -s tests -v
```

The first command looks for conflicts between installed packages. The second runs three small tests: they check that the bot imports, creates proxy sessions, and parses HTML for link previews.

No real token is needed, no network connections are made, and your vault is not changed. These tests do not check message saving or recognition. If a check fails, include its output when reporting the problem, but do not publish tokens or passwords from `config.py`.

## Usage

1. Send/forward messages that should be added to your Obsidian vault directly to your bot or to your private Telegram group.

2. Run the bot from a terminal with the environment activated:
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
