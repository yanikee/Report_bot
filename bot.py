import os
import aiofiles
from discord import Intents, CustomActivity, Status
from discord.ext import commands

from colorama import Fore, Style, init
from modules.cogs import get_cogs



init(autoreset=True)

class ReportBot(commands.Bot):
  def __init__(self):
    intents = Intents.none()
    intents.messages = True
    intents.guilds = True
    super().__init__(command_prefix="!!!!!!!!!!!!!!!!!!!!!!!!!//!", intents=intents)


  def log(self, message: str, level: str = "INFO"):
    colors = {"INFO": Fore.CYAN, "SUCCESS": Fore.GREEN, "WARN": Fore.YELLOW, "ERROR": Fore.RED}
    prefix = f"{Style.DIM}[{level}]{Style.RESET_ALL}"
    print(f"{prefix} {colors.get(level, Fore.WHITE)}{message}")

  async def get_version(self) -> str:
    """バージョンファイルを読み込む、または作成する"""
    path = "db/bot_version.txt"
    if os.path.exists(path):
      async with aiofiles.open(path, mode="r", encoding="UTF-8") as f:
        return (await f.read()).strip()
    else:
      async with aiofiles.open(path, mode="w", encoding="UTF-8") as f:
        await f.write("None")
      return "None"

  async def setup_hook(self):
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== Initializing ReportBot ===\n")

    # Cog読み込み
    for cog in get_cogs():
      await self.load_extension(cog)
      self.log(f"Loaded extension: {cog}", "INFO")

    await self.tree.sync()
    self.log("Slash commands synchronized.", "SUCCESS")

    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== Setup Hook Complete ===\n")


  async def on_ready(self):
    version = await self.get_version()

    custom_activity = CustomActivity(f"/help | ver{version}")
    await self.change_presence(status=Status.online, activity=custom_activity)

    self.log(f"Logged in as {self.user}", "SUCCESS")

    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== On Ready Complete ===\n")