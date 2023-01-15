# Bot token issued by @botfather (Telegram)
token = 'xxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Path to the folder where new notes should be created
inbox_path = r'C:\your-obsidian-vault'

# Path to the folder where received pictures should be stored
photo_path = r'C:\your-obsidian-vault\attachments'

# If True, messages (including picture captions) will retain formatting (bold, italic, links, etc.)
# If False, messages will be saved as plain text. This also removes inline links.
format_messages = True

# If True, voice messages will be recognized to text.
# This requires Whisper ( https://github.com/openai/whisper ), FFMPEG, Python and PyTorch to be installed
# on the machine where the script is running.
# If False, voice messages will not be recognized nor stored.
recognize_voice = False

# Whisper speech recognition software's model options and their relative speed and size of DB:
# tiny (x32, 78MB), base(x16, 145MB), small(x6, 484MB), medium(x2, 1.5GB), large(x1, 3.1GB).
# These are general models. English-only models also exist. Check https://github.com/openai/whisper .
whisper_model = 'medium'

# The following set of options define file name of the note where Telegram posts appear.
# Resulting file name consists of concatenated prefix, date, and postfix.
# With the default config values, full note name would be like Telegram-2023-01-02_Notes.md.
# To omit either prefix or postfix (or both), comment out corresponding option with # or edit it to be empty.
# To omit the date part and always put new messages in a single static file, comment out note_date option
# or edit it to be empty.
note_prefix = 'Telegram-'
note_date = True
note_postfix = '_Notes'

# The following parameter sets logging level:
# 0 - Disable any logging. The only traces of the program are notes and files in the vault.
# 1 - Basic logging of the main actions and errors in the `bot.log` file in the script folder.
# 2 - Extended logging: the same as basic + recording of incoming messages to
# `messages-YYYY-MM-DD.txt` file in the script folder in order to help debugging the script.
log_level = 2

# If True, then all line breaks are removed from the note, and any note literally becomes one-line note.
# If False, then the note is stored including all line breaks.
one_line_note = False

# If one of the specified substrings is found in the message text (case insensitive),
# the message will be converted to a Markdown task like the following:
# - [ ] Complete one important task
# To turn this off, specify task_keywords = {}
task_keywords = {'задач', 'сделать', 'todo', 'complete'}

# If one of the keywords is found in the message text, the specified tag will be added to the message
# To turn this off, specify negative_keywords = {}
negative_keywords = {'негатив', 'печал'}
negative_tag = '#негатив'

# The ID of the chat the bot should read. Messages from other chats will be ignored.
# When the bot receives the /start command, it replies with the ID of the chat.
# This setting is not in effect yet.
# my_chat_id = -xxxxxxxxx
