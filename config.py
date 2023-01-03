# Bot token issued by @botfather
token = 'xxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Path to the folder where new notes should be created
inbox_path = r'C:\your-obsidian-vault'

# Path to the folder where received pictures should be stored
photo_path = r'C:\your-obsidian-vault\attachments'

# If True, messages (including picture captions) will retain formatting (bold, italic, links, etc.)
# If False, messages will be saved as plain text. This also removes inline links.
format_messages = True

# If True, voice messages will be recognized to text.
# This requires Whisper and FFMPEG to be installed on the machine where the script is running.
# If False, voice messages will not be recognized nor stored.
recognize_voice = False

# Note file name prefix and postfix which surround the date in YYYY-MM-DD format
# With the default config values, full note name would be like Telegram-2023-01-02_Notes.md
# To omit either part (or both), assign a blank value: note_postfix = ''
note_prefix = 'Telegram-'
note_postfix = '_Notes'

# If one of the specified substrings is found in the message text (case insensitive),
# the message will be converted to a Markdown task like the following:
# - [ ] Сделать одно важное дело
# To turn this off, specify task_keywords = {}
task_keywords = {'задач', 'сделать', 'todo'}

# If one of the keywords is found in the message text, the specified tag will be added to the message
# To turn this off, specify negative_keywords = {}
negative_keywords = {'негатив', 'печал'}
negative_tag = '#негатив'

# The ID of the chat the bot should read. Messages from other chats will be ignored.
# When the bot receives the /start command, it replies with the ID of the chat.
# This setting is not in effect yet.
# my_chat_id = -xxxxxxxxx
