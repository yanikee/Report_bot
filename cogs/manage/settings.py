from discord.ext import commands
from discord import app_commands, ui
import discord

from typing import Literal

from modules import error
from const import EMOJI_DICT
from modules.db import DB, GuildSettings


class Settings(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.db = DB()
    self.data: dict[int, GuildSettings] = {}

  @app_commands.command(name="settings", description='設定を行います')
  @discord.app_commands.guild_only()
  async def settings(self, interaction:discord.Interaction):
    guild = interaction.guild
    if not guild:
      return

    guild_data = await self.db.get_guild_settings(guild.id)
    if not guild_data:
      guild_data = await self.db.create_guild_settings(guild.id)


    self.data[guild.id] = guild_data

    view = self.settings_page_1()
    await interaction.response.send_message(view=view, ephemeral=True)


  def settings_page_1(self):
    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("**settings (1/3)**\n"
                                      "1. Report機能\n"
                                      "1. 匿名Ticket機能\n"
                                      "これらの設定を行います"))
    row = ui.ActionRow()
    row.add_item(ui.Button(label="次へ", emoji=EMOJI_DICT["arrow_forward"], custom_id=f"settings_page_2", style=discord.ButtonStyle.gray))
    container.add_item(row)

    view = ui.LayoutView()
    view.add_item(container)
    return view


  async def settings_page_2(self, interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
      return


    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("**settings (2/3)**\n## Report機能の設定"))

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    row1 = ui.ActionRow()
    default_values = await self.get_fetch_channel(guild, self.data[guild.id]["report_channel_id"])
    row1.add_item(ui.ChannelSelect(
      placeholder="Report送信チャンネル",
      channel_types=[discord.ChannelType.text],
      custom_id=f"settings_report_channel",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row1)

    row2 = ui.ActionRow()
    default_values = await self.get_fetch_role(guild, self.data[guild.id]["report_mention_role_id"])
    row2.add_item(ui.RoleSelect(
      placeholder="Report送信時メンションロール",
      custom_id=f"settings_report_mention_role",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row2)

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    row3 = ui.ActionRow()
    row3.add_item(ui.Button(label="戻る", emoji=EMOJI_DICT["arrow_back"], custom_id=f"settings_page_1", style=discord.ButtonStyle.gray))
    row3.add_item(ui.Button(label="次へ", emoji=EMOJI_DICT["arrow_forward"], custom_id=f"settings_page_3", style=discord.ButtonStyle.gray))
    container.add_item(row3)

    view = ui.LayoutView()
    view.add_item(container)

    await interaction.response.edit_message(view=view)


  async def settings_page_3(self, interaction:discord.Interaction):
    guild = interaction.guild
    if not guild:
      return

    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("**settings (3/3)**\n## Ticket機能の設定"))

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    row1 = ui.ActionRow()
    default_values = await self.get_fetch_channel(guild, self.data[guild.id]["ticket_channel_id"])
    row1.add_item(ui.ChannelSelect(
      placeholder="Ticket送信チャンネル",
      channel_types=[discord.ChannelType.text],
      custom_id=f"settings_ticket_channel",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row1)

    row2 = ui.ActionRow()
    default_values = await self.get_fetch_role(guild, self.data[guild.id]["ticket_mention_role_id"])
    row2.add_item(ui.RoleSelect(
      placeholder="Ticket送信時メンションロール",
      custom_id=f"settings_ticket_mention_role",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row2)

    row3 = ui.ActionRow()
    default_values = await self.get_fetch_channel(guild, self.data[guild.id]["ticket_button_channel_id"])
    row3.add_item(ui.ChannelSelect(
      placeholder="Ticket開始ボタンを設置するチャンネル",
      custom_id=f"settings_ticket_button_channel",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row3)

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    row3 = ui.ActionRow()
    row3.add_item(ui.Button(label="戻る", emoji=EMOJI_DICT["arrow_back"], custom_id=f"settings_page_2", style=discord.ButtonStyle.gray))
    row3.add_item(ui.Button(label="保存して終了", emoji=EMOJI_DICT["arrow_forward"], custom_id=f"settings_page_3", style=discord.ButtonStyle.gray))
    container.add_item(row3)

    view = ui.LayoutView()
    view.add_item(container)

    await interaction.response.edit_message(view=view)


  async def get_fetch_channel(self, guild: discord.Guild, channel_id: int | None) -> list[discord.abc.GuildChannel | discord.Thread]:
    if not channel_id:
      return []

    channel = guild.get_channel(channel_id)
    if not channel:
      try:
        channel = await guild.fetch_channel(channel_id)
      except Exception:
        return []

    return [channel]

  async def get_fetch_role(self, guild: discord.Guild, role_id: int | None) -> list[discord.Role]:
    if not role_id:
      return []

    role = guild.get_role(role_id)
    if not role:
      try:
        role = await guild.fetch_role(role_id)
      except Exception:
        return []

    return [role]

  @commands.Cog.listener()
  async def on_interaction(self, interaction: discord.Interaction):
    if not interaction.data:
      return

    custom_id = interaction.data.get("custom_id")
    if not custom_id:
      return

    # settings_1
    if custom_id == "settings_page_1":
      view = self.settings_page_1()
      await interaction.response.edit_message(view=view)

    # settings_2
    elif custom_id == "settings_page_2":
      await self.settings_page_2(interaction)

    # settings_3
    elif custom_id == "settings_page_3":
      await self.settings_page_3(interaction)





async def setup(bot):
  await bot.add_cog(Settings(bot))