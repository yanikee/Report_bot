from discord.ext import commands
from discord.ext import tasks

import datetime
import aiofiles



JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")

class GuildCountRecorder(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.record_guild_count.start()

  @tasks.loop(time=datetime.time(hour=23, minute=58, tzinfo=JST))
  async def record_guild_count(self):
    # サーバー数を取得
    guild_count = len(self.bot.guilds)
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    #CSVファイルにサーバー数を追記
    async with aiofiles.open('db/guild_counts.csv', mode='a') as csvfile:
      await csvfile.write(f'\n{today},{guild_count}')



async def setup(bot):
  await bot.add_cog(GuildCountRecorder(bot))