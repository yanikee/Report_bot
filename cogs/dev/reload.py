from discord.ext import commands
from discord import app_commands
import discord

from modules import cogs
from bot import ReportBot



cog_list = cogs.get_cogs()
dev_cog_list = cogs.get_dev_cogs()
cog_list += dev_cog_list

class Reload(commands.Cog):
  def __init__(self, bot: ReportBot):
    self.bot = bot

  @app_commands.command(name="reload",description="[開発者専用]cogをreloadします"  )
  @app_commands.choices(cog=[app_commands.Choice(name=x, value=x) for x in cog_list])
  @app_commands.describe(cog="reloadしたいCogを選択")
  async def reload(self, interaction: discord.Interaction, cog: app_commands.Choice[str]):
    if not await self.bot.is_owner(interaction.user):
      return await interaction.response.send_message("このコマンドは開発者専用です", ephemeral=True)

    try:
      await self.bot.reload_extension(cog.value)
    except Exception as e:
      await interaction.response.send_message(f"- {cog.value}の再読み込みに失敗\n - 理由：{e}", ephemeral=True)
      return

    await interaction.response.send_message(f"{cog.value}の再読み込みに成功", ephemeral=True)
    await self.bot.tree.sync()
    print(f"リロード完了：{cog.value}")



async def setup(bot):
  await bot.add_cog(Reload(bot))