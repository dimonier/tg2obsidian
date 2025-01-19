# Bot token issued by @botfather (Telegram)
token = 'xxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# The IDs of chats the bot should read, separated by colons. Messages from other chats will be ignored.
# A single chat can be specified like '123456789'.
# Multiple chats can be specified like '123456789:987654321:111222333'.
# When the bot receives the /start command in any chat, it replies with that chat's ID which can be added here.
allowed_chats = '123456789:987654321'

# Path to the folder where new notes should be created
inbox_path = r'C:\your-obsidian-vault'

# Path to the folder where received pictures should be stored
photo_path = r'C:\your-obsidian-vault\attachments'

# If True, messages (including picture captions) will retain formatting (bold, italic, links, etc.)
# If False, messages will be saved as plain text. This also removes inline links.
format_messages = True

# Minimum time interval (in seconds) between messages to add timestamp
message_timestamp_interval = 5

# If True, messages will be deleted after processing.
delete_messages = False

#if True, callout block containing link information such as description and/or image will be created
# for messages containing single url
#if False, or more than one url in the message, no callout will be created
create_link_info = True

# Time zone for time stamp formatting
time_zone = 'Europe/Moscow'

# If True, optical character recognition (OCR) will be performed on images.
# This requires tesseract (https://github.com/tesseract-ocr/tessdoc) to be installed and added to PATH
# If False, OCR will not be applied to received images.
ocr = False

# One or more languages to use for OCR. Defaults to 'eng'. Few languages should be delimited with +.
ocr_languages = 'rus+eng'

# If True, voice messages will be recognized to text.
# This requires Whisper ( https://github.com/openai/whisper ), FFMPEG, Python and PyTorch to be installed
# on the machine where the script is running.
# If False, voice messages will not be recognized nor stored.
recognize_voice = False

# Whisper speech recognition software's model options and their relative speed and size of DB:
# tiny (x32, 78MB), base(x16, 145MB), small(x6, 484MB), medium(x2, 1.5GB), large(x1, 3.1GB).
# These are general models. English-only models also exist. Check https://github.com/openai/whisper
whisper_model = 'medium'

# Setting up the device for Whisper
# By default, CPU is used. Other possible values: cuda
whisper_device = 'cpu'
#whisper_device = 'cuda'

# Note filename template. Available variables: {year}, {month}, {day}
# With the default template, the resulting filename will have the format Telegram-2023-01-02.md
note_name_template = 'Telegram-{year}-{month}-{day}'

# The following parameter sets logging level:
# 0 - Disable any logging. The only traces of the program are notes and files in the vault.
# 1 - Basic logging of the main actions and errors in the `bot.log` file in the script folder.
# 2 - Extended logging: the same as basic + recording of incoming messages to
# `messages-YYYY-MM-DD.txt` file in the script folder in order to help debugging the script.
log_level = 2

# If True, then all line breaks are removed from the note, and any note literally becomes one-line note.
# If False, then note is stored including all line breaks.
one_line_note = False

# If one of the specified substrings is found in the message text (case insensitive),
# the message will be converted to a Markdown task like the following:
# - [ ] Complete one important task
# To turn this off, specify task_keywords = {}
task_keywords = {'задач', 'сделать', 'todo', 'complete'}

# If one of the keywords is found in the message text, the specified tag will be added to the message
# To turn this off, specify negative_keywords = {}
negative_keywords = {'негатив', 'печал'}

# Tag to add to the text where a keyword is detected
negative_tag = '#негатив'

