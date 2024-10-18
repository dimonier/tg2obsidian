# tests/test_config.py
import os

# Получаем абсолютный путь к директории tests
tests_dir = os.path.dirname(os.path.abspath(__file__))

token = "TEST_BOT_TOKEN"
my_chat_id = 123456789
inbox_path = os.path.join(tests_dir, "test_data", "inbox")
photo_path = os.path.join(tests_dir, "test_data", "photos")
time_zone = "Europe/Moscow"
note_name_template = "{year}-{month}-{day}"
task_keywords = ["TODO", "FIXME", "IMPORTANT"]
negative_keywords = ["BAD", "AWFUL", "TERRIBLE"]
negative_tag = "#negative"
ocr = False
recognize_voice = False
format_messages = True
create_link_info = False
log_level = 0

# + все остальные необходимые параметры из основного config.py