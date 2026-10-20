"""Offline smoke tests for the documented basic installation.

Each check runs in a fresh process and temporary directory: importing the bot
initializes SQLite/logging, and network access must never reach Telegram.
"""

from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = """
import importlib.util
from pathlib import Path
import sys

def block_network(event, args):
    if event in {
        'socket.connect', 'socket.getaddrinfo',
        'socket.gethostbyname', 'socket.gethostbyaddr',
    }:
        raise AssertionError(f'Network access is forbidden: {event}')

sys.addaudithook(block_network)
root = Path(sys.argv[1])
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location('config', root / 'config.py')
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
config.token = '123456789:offline_test_token_not_a_real_telegram_token'
config.ocr = False
config.recognize_voice = False
config.log_level = 0
config.telegram_proxy_url = ''
config.telegram_proxy_login = ''
config.telegram_proxy_password = ''
config.inbox_path = str(Path.cwd() / 'vault')
config.photo_path = str(Path.cwd() / 'attachments')
sys.modules['config'] = config

import tg2obsidian_bot as app
"""


class InstallationTests(unittest.TestCase):
    def run_offline(self, code):
        with tempfile.TemporaryDirectory(prefix='tg2obsidian-test-') as directory:
            result = subprocess.run(
                [sys.executable, '-B', '-c', BOOTSTRAP + textwrap.dedent(code), str(ROOT)],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=60,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bot_imports_without_recognition_packages(self):
        self.run_offline("""
            from aiogram import Bot, Dispatcher

            assert isinstance(app.bot, Bot)
            assert isinstance(app.dp, Dispatcher)
            assert app.bot.default.parse_mode == 'HTML'
            assert Path('bot_settings.db').is_file()
            for module in ('torch', 'whisper', 'pytesseract', 'openai'):
                assert module not in sys.modules, module
        """)

    def test_proxy_sessions_can_be_created_without_network(self):
        self.run_offline("""
            import asyncio
            from aiohttp_socks import ProxyConnector

            config.telegram_proxy_url = 'socks5h://127.0.0.1:1080'

            async def check():
                telegram = app.create_bot_session()
                try:
                    session = await telegram.create_session()
                    assert isinstance(session.connector, ProxyConnector)
                    async with app.create_telegram_http_session() as download:
                        assert isinstance(download.connector, ProxyConnector)
                finally:
                    await telegram.close()
                    await app.bot.session.close()

            asyncio.run(check())
        """)

    def test_link_preview_parser_is_available(self):
        self.run_offline("""
            props = app.get_open_graph_props(
                '<html><head><title>Offline page</title>'
                '<meta property="og:description" content="Example description">'
                '</head></html>'
            )
            assert props['title'] == 'Offline page'
            assert props['description'] == 'Example description'
        """)


if __name__ == '__main__':
    unittest.main()
