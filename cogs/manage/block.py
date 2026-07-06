from discord.ext import commands
from discord import app_commands
import discord

from modules import error
from modules.db import DB
from bot import ReportBot



class Block(commands.Cog):
  def __init__(self, bot: ReportBot):
    self.bot = bot
    self.db = DB()

  @app_commands.command(name="block", description='匿名Report, 匿名Ticketをブロック/ブロック解除します')
  @app_commands.choices(block_type=[
    app_commands.Choice(name="このスレッドのブロック", value="normal"),
    app_commands.Choice(name="サーバー全体のブロック", value="server"),
  ])
  @app_commands.describe(block_type="ブロックの種類を選ぶ")
  @discord.app_commands.guild_only()
  async def block(self, interaction: discord.Interaction, block_type: app_commands.Choice[str]):
    guild, channel = (interaction.guild, interaction.channel)
    if not guild or not channel:
      msg = "サーバーのスレッド内で実行してください"
      await error.send_error(msg, interaction)
      return

    if not isinstance(channel, discord.Thread):
      msg = "サーバーのスレッド内で実行してください"
      await error.send_error(msg, interaction)
      return

    await interaction.response.defer(thinking=True)

    thread = await self.db.get_thread(channel.id)
    if not thread:
      msg = "スレッドデータが取得できませんでした"
      await error.send_error(msg, interaction, followup=True)
      return

    user_id = thread["user_id"]

    if block_type.value == "server":
      is_blocked = await self.db.toggle_guild_block(guild.id, user_id)
      color=0xff0000
      if is_blocked:
        description="## サーバーブロック済み\nこのユーザーはサーバー内で本botの全ての機能を利用できません"
      else:
        description="## サーバーブロック解除\nこのユーザーのサーバーブロックが解除されました"

    else:
      is_blocked = await self.db.toggle_thread_block(channel.id)
      color=0xffcc00
      if is_blocked:
        description="## スレッド内ブロック済み\nこのユーザーはこのスレッド内にのみ返信できません"
      else:
        description="## スレッド内ブロック解除\nこのユーザーのスレッド内ブロックが解除されました"

    embed = discord.Embed(
      description=description,
      color=color,
    )

    await interaction.followup.send(embed=embed)
    return



async def setup(bot):
  await bot.add_cog(Block(bot))