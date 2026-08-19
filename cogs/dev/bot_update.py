from datetime import datetime

import aiofiles
from discord import (
  CustomActivity,
  Embed,
  Interaction,
  Status,
  TextChannel,
  app_commands,
)
from discord.ext import commands

from bot import ReportBot


class BotUpdate(commands.GroupCog, group_name='update'):
  def __init__(self, bot: ReportBot):
    self.bot = bot

  @app_commands.command(
    name="report_bot",
    description="[開発者専用]Report bot! のアップデート"
  )
  @app_commands.describe(channel="送信するチャンネルを選択してください")
  @app_commands.describe(version="バージョンを指定してください")
  @app_commands.describe(description="本文を入力してください")
  async def update_bot(self, interaction: Interaction, version: str, description: str, channel:TextChannel | None = None):
    if not await self.bot.is_owner(interaction.user):
      await interaction.response.send_message("このコマンドは開発者専用です", ephemeral=True)
      return

    if not channel:
      if not isinstance(interaction.channel, TextChannel):
        return

      channel = interaction.channel

    embed = Embed(
      title = f"__Report bot! ver{version}__",
      url = channel.jump_url,
      description = description,
      color=0xffe7ab,
      timestamp=datetime.now(),
    )
    embed.set_footer(
      text = "\u200b",
      icon_url = self.bot.user.avatar.url, # type: ignore
    )
    await interaction.response.send_message(f"{channel.mention}に送ったよう", ephemeral=True)
    await channel.send(embed=embed)

    path = "db/bot_version.txt"
    async with aiofiles.open(path, mode="w") as f:
      await f.write(version)
    custom_activity = CustomActivity(f"/help | ver{version}")
    await self.bot.change_presence(status=Status.online, activity=custom_activity)



async def setup(bot):
  await bot.add_cog(BotUpdate(bot))
