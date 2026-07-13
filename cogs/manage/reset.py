from discord import ButtonStyle, Interaction, app_commands, ui
from discord.ext import commands

from bot import ReportBot
from modules.db import DB, GuildSettings
from modules.types import GuildSettingsWrite


class Reset(commands.Cog):
  def __init__(self, bot: ReportBot):
    self.bot = bot
    self.db = DB()
    self.data: dict[int, GuildSettings] = {}


  @app_commands.command(name="reset", description='サーバーの設定をリセットします。')
  @app_commands.guild_only()
  async def reset(self, interaction: Interaction):
    guild = interaction.guild
    if not guild:
      return

    await interaction.response.defer(ephemeral=True)

    guild_data = await self.db.get_guild_settings(guild.id)
    if not guild_data:
      guild_data = await self.db.create_guild_settings(guild.id)

    self.data[guild.id] = guild_data

    view = self.confirm_reset()
    await interaction.followup.send(view=view)


  def confirm_reset(self) -> ui.LayoutView:
    container = ui.Container(accent_color=0xff0000)
    container.add_item(ui.TextDisplay("サーバーの設定をリセットします。よろしいですか？"))
    row = ui.ActionRow()
    row.add_item(ui.Button(label="はい", custom_id="reset_yes", style=ButtonStyle.red))
    row.add_item(ui.Button(label="いいえ", custom_id="reset_no", style=ButtonStyle.gray))
    container.add_item(row)

    view = ui.LayoutView()
    view.add_item(container)
    return view


  @commands.Cog.listener()
  async def on_interaction(self, interaction: Interaction):
    guild = interaction.guild
    if not guild:
      return

    message = interaction.message
    if not message:
      return


    if not interaction.data:
      return

    custom_id = interaction.data.get("custom_id")
    if not custom_id:
      return

    # page
    if "reset_yes" in custom_id:
      await interaction.response.defer()

      data: GuildSettingsWrite = {
        "guild_id": guild.id,
        "report_channel_id": None,
        "report_mention_role_id": None,
        "ticket_channel_id": None,
        "ticket_button_channel_id": None,
        "ticket_mention_role_id": None,
      }

      await self.db.upsert_guild_settings(data)

      container = ui.Container(accent_color=0x00ff00)
      container.add_item(ui.TextDisplay("リセットしました。`/settings`コマンドで再設定をしましょう。"))

      view = ui.LayoutView()
      view.add_item(container)
      await interaction.edit_original_response(view=view)
      return

    if "reset_no" in custom_id:
      await interaction.response.defer()
      await interaction.delete_original_response()
      return



async def setup(bot):
  await bot.add_cog(Reset(bot))
