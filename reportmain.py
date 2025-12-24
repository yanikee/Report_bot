from discord.ext import commands
import discord

import os
import logging
import aiofiles
import argparse

from modules import cogs
from const import TOKEN


parser = argparse.ArgumentParser(description="report_bot!を起動する")
parser.add_argument("-dev", action="store_true", help="開発モードで実行")
parser.add_argument("-reset", action="store_true", help="何も読み込まない")
args = parser.parse_args()

if args.dev:
  cog_list = cogs.get_cogs()
  dev_cog_list = cogs.get_dev_cogs()
elif args.reset:
  cog_list = []
  dev_cog_list = None
else:
  cog_list = cogs.get_cogs()
  dev_cog_list = None




intents = discord.Intents.none()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!!!!!", intents=intents)


@bot.event
async def on_ready():
  for x in cog_list:
    await bot.load_extension(x)
    print(f"ロード完了：{x}")

  if dev_cog_list:
    for x in dev_cog_list:
      await bot.load_extension(x)
      print(f"ロード完了：{x}")

  await bot.tree.sync()
  print("全ロード完了")


  path = "db/bot_version"
  if os.path.exists(path):
    async with aiofiles.open(path, mode="r", encoding="UTF-8") as f:
      version = await f.read()
  else:
    version = "None"
    async with aiofiles.open(path, mode="w", encoding="UTF-8") as f:
      await f.write(version)

  custom_activity = discord.CustomActivity(f"/help | ver{version}")
  await bot.change_presence(status=discord.Status.online, activity=custom_activity)


bot.run(TOKEN, log_level = logging.WARNING)