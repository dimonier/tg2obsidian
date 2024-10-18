import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot, types
# import warnings
# warnings.filterwarnings("ignore", category=DeprecationWarning)

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests import test_config

# # Патчим config перед импортом tg2obsidian_bot
# with patch.dict('sys.modules', {'config': test_config}):
#     import tg2obsidian_bot

# Мокаем Bot перед импортом tg2obsidian_bot
with patch('aiogram.Bot', return_value=AsyncMock()) as mock_bot:
    import tg2obsidian_bot

@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    return bot

@pytest.fixture
def mock_message():
    message = MagicMock(spec=types.Message)
    message.from_user = MagicMock(spec=types.User)
    message.chat = MagicMock(spec=types.Chat)
    message.reply = AsyncMock()
    message.from_user.full_name = "Test User"  # Добавление атрибута full_name
    return message

### Инициализация бота
@pytest.fixture
def bot():
    with patch('aiogram.Bot', return_value=AsyncMock()) as mock_bot:
        mock_bot.return_value.token = test_config.token  # Установка значения токена
        yield mock_bot

def test_bot_initialization(bot):
    assert bot.return_value.token == test_config.token, "Bot token should match the test configuration"

## Команды

### /start

@pytest.mark.asyncio
async def test_send_welcome(mock_bot, mock_message):
    mock_message.from_user.username = "test_user"
    mock_message.from_user.first_name = "Test"
    mock_message.from_user.last_name = "User"
    mock_message.from_user.id = 123456
    mock_message.chat.id = 789012
    mock_message.chat.title = "Test Chat Title"

    await tg2obsidian_bot.send_welcome(mock_message)

    expected_reply = "Hello Test User!\n\nI`m a private bot, I save messages from a private Telegram group to Obsidian inbox.\n\nYour Id: 123456\nThis chat Id: 789012\n"
    mock_message.reply.assert_called_once_with(expected_reply)

### /help

@pytest.mark.asyncio
async def test_help_command(mock_bot, mock_message):
    mock_message.text = '/help'
    mock_message.from_user.id = test_config.my_chat_id

    reply_text = '''/start - start Bot
    /help - show this help
    a text or picture message - to be passed into Obsidian inbox
    an audio message - to be recognized and passed into Obsidian inbox as text
    '''
    await tg2obsidian_bot.help(mock_message)
    mock_message.reply.assert_called_once_with(reply_text)

### Обработка сообщений

@pytest.mark.asyncio
async def test_process_message():
    # Создаем мок-объект для сообщения
    mock_message = MagicMock(spec=types.Message)
    mock_message.message_id = 123456
    mock_message.chat = MagicMock()  # Создаем мок для chat
    mock_message.chat.id = test_config.my_chat_id
    mock_message.from_user = MagicMock()  # Создаем мок для from_user
    mock_message.from_user.id = 987654321
    mock_message.from_user.username = "test_user"
    mock_message.text = "Тестовое сообщение"
    mock_message.link_preview_options = MagicMock()
    mock_message.link_preview_options.url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Мокаем функции, которые вызываются внутри process_message
    with patch('tg2obsidian_bot.log_basic') as mock_log_basic, \
         patch('tg2obsidian_bot.log_message') as mock_log_message, \
         patch('tg2obsidian_bot.note_from_message') as mock_note_from_message, \
         patch('tg2obsidian_bot.get_forward_info') as mock_get_forward_info, \
         patch('tg2obsidian_bot.embed_formatting') as mock_embed_formatting, \
         patch('tg2obsidian_bot.save_message') as mock_save_message, \
         patch('tg2obsidian_bot.bot.set_message_reaction') as mock_set_message_reaction:

        # Настраиваем возвращаемые значения для моков
        mock_note_from_message.return_value = MagicMock()
        mock_get_forward_info.return_value = ""
        mock_embed_formatting.return_value = "Отформатированное сообщение"

        # Вызываем тестируемую функцию
        await tg2obsidian_bot.process_message(mock_message)

        # Проверяем, что нужные функции были вызваны
        mock_log_basic.assert_called_once()
        mock_log_message.assert_called_once_with(mock_message)
        mock_note_from_message.assert_called_once_with(mock_message)
        mock_get_forward_info.assert_called_once_with(mock_message)
        mock_embed_formatting.assert_called_once_with(mock_message)
        mock_save_message.assert_called_once()
        mock_set_message_reaction.assert_called_once()

        # Проверяем содержимое сохраненного сообщения
        saved_note = mock_save_message.call_args[0][0]
        assert saved_note.text == "Отформатированное сообщение\n![https://www.youtube.com/watch?v=dQw4w9WgXcQ](https://www.youtube.com/watch?v=dQw4w9WgXcQ)\n"

# Дополнительные тесты для других типов сообщений (фото, стикер, голосовое и т.д.) можно добавить здесь.
# Но это не нужно, так как другие типы сообщений обрабатываются в других функциях.