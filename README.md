# tg2obsidian

This program ("Bot") uses Telegram's free bot functionality in order to save messages from a Telegram group to the [Obsidian](https://obsidian.md) vault on your local computer.

The Markdown markup used will also work for most [other programs](https://www.markdownguide.org/tools/) that work with local Markdown files.

The Bot is designed to run locally on the computer where the Obsidian files are located.

This readme is also available [in Russian](README.ru.md).

## Use case

- You are typing or recording messages in your personal Telegram group _on the go_
- Bot receives new messages from Telegram and saves them as Inbox notes in your PKM vault
- _Afterwards, in a quiet environment_, you process those notes, moving the information from them to appropriate places in your vault

## Features

- All messages are grouped by date — one note per day.
- Each message in a note has a header with a date and time stamp.
- Formatting of messages and captions is preserved.
- For forwarded messages, information about the origin is added.
- Pictures and files are saved to the vault and embedded in the note.
- For contacts, YAML front matter and vcard are saved.
- It is possible to convert notes with certain keywords into a task.
- It is possible to tag notes with certain keywords.
- It is possible to recognize speech from the notes. In this case, the Bot sends the recognized text as a response to the original voice message.

## Set up

1. Install [Python](https://python.org) 3.10+
2. install script dependencies:

```shell
pip install -r requirements.txt
```

3. Install Whisper module if you need voice messages get recognized to text:

```shell
pip install git+https://github.com/openai/whisper.git
```

4. Install compiled [FFMPEG](https://ffmpeg.org/download.html) and add the path to the executable (in Windows — ffmpeg.exe) to the `path` environment variable. Go to the folder containing this script and make sure that `ffmpeg.exe` could be started there.
5. Create your own bot using https://t.me/BotFather
6. Paste the token received from `@botfather` into the appropriate parameter in `config.py` and change the rest of the parameters in `config.py` as desired.
7. Add the bot created above to a private Telegram group and make it administrator so it can read messages.

## Usage

1. Send or forward to the private Telegram group messages that should go to your Obsidian vault.

2. Run Bot:
```shell.
python tg2obsidian_bot.py
```

- You can keep Bot running indefinitely on a computer or server that is permanently turned on. In this case, it will recognize speech and create/update notes in Obsidian in real time.
- If you only turn your computer on when you're using it, run Bot directly when you need to get Obsidian messages, and close the program when you've received all the messages.

After launch, Bot creates `bot.log` file in the script folder, where the main actions and errors are logged.

In addition, all incoming messages are recorded to `messages-YYYYY-MM-DD.txt` file in the script folder in order to help debugging the script. They are not necessary for the operation of Bot, so you can safely delete them if needed.
## Known issues

1. If a message contains both emoji and formatting, positions where the formatting is applied may be inaccurate. If you have a lot of such issues, you can disable formatting in config.

## Support author

If you would like to thank the author of this project, your donations will be gratefully accepted here: https://pay.cloudtips.ru/p/1f9bf82f

![](qrCode.png)
