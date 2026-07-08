from os.path import exists

from pyrogram import Client, enums
from pyrogram.types import BotCommand

if exists("./config.py"):
    from config import LOGGER, Config
else:
    from sample_config import LOGGER, Config

from user import User

BOT_COMMANDS = [
    BotCommand("start", "Show the welcome message and help"),
    BotCommand("help", "Explain how the bot works"),
    BotCommand("chat", "Set the target chat, e.g. /chat -100xxxxxxxxxx"),
    BotCommand("delay", "Set a delay between deletions, e.g. /delay 10"),
    BotCommand("purge", "Find and delete duplicate media in the target chat"),
]


class Bot(Client):
    USER: User = None
    USER_ID: int = None

    def __init__(self):
        super().__init__(
            "oxmohsen_bot",
            api_hash=Config.API_HASH,
            api_id=Config.APP_ID,
            bot_token=Config.TG_BOT_TOKEN,
            sleep_threshold=0,
            plugins={"root": "plugins"},
        )
        self.LOGGER = LOGGER

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        usr_bot_me = await self.get_me()
        self.set_parse_mode(enums.ParseMode.HTML)
        await self.set_bot_commands(BOT_COMMANDS)
        self.LOGGER(__name__).info(
            f"Bot {usr_bot_me.first_name} (@{usr_bot_me.username}) started!"
        )
        self.USER, self.USER_ID = await User().start()

    async def stop(self, *args):
        if self.USER:
            await self.USER.stop()
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped. Bye.")
