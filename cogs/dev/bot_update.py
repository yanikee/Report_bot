from discord import app_commands
from discord.ext import commands
import discord

from datetime import datetime
import aiofiles
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
  async def update_bot(self, interaction: discord.Interaction, version: str, description: str, channel:discord.TextChannel | None = None):
    if not await self.bot.is_owner(interaction.user):
      await interaction.response.send_message("このコマンドは開発者専用です", ephemeral=True)
      return

    if not channel:
      if not isinstance(interaction.channel, discord.TextChannel):
        return

      channel = interaction.channel

    embed = discord.Embed(
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

    path = "data/bot_version.txt"
    async with aiofiles.open(path, mode="w") as f:
      await f.write(version)
    custom_activity = discord.CustomActivity(f"/help | ver{version}")
    await self.bot.change_presence(status=discord.Status.online, activity=custom_activity)



async def setup(bot):
  await bot.add_cog(BotUpdate(bot))