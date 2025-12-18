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


  def settings_page_1(self) -> ui.LayoutView:
    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("**settings (1/3)**\n"
                                      "1. Report機能\n"
                                      "1. Ticket機能\n"
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

    container.add_item(ui.TextDisplay("**Reportを作成するチャンネル**"))
    row1 = ui.ActionRow()
    default_values = await self.get_fetch_channel(guild, self.data[guild.id]["report_channel_id"])
    row1.add_item(ui.ChannelSelect(
      placeholder="チャンネルを選択（任意）",
      channel_types=[discord.ChannelType.text],
      custom_id=f"settings_report_channel",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row1)

    container.add_item(ui.TextDisplay("**Report作成時にメンションするロール**"))
    row2 = ui.ActionRow()
    default_values = await self.get_fetch_role(guild, self.data[guild.id]["report_mention_role_id"])
    row2.add_item(ui.RoleSelect(
      placeholder="ロールを選択（任意）",
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

    container = ui.Container(accent_color=0xc8e1ff)
    container.add_item(ui.TextDisplay("**settings (3/3)**\n## Ticket機能の設定"))

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    container.add_item(ui.TextDisplay("**Tiekctを作成するチャンネル**"))
    row1 = ui.ActionRow()
    default_values = await self.get_fetch_channel(guild, self.data[guild.id]["ticket_channel_id"])
    row1.add_item(ui.ChannelSelect(
      placeholder="チャンネルを選択（任意）",
      channel_types=[discord.ChannelType.text],
      custom_id=f"settings_ticket_channel",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row1)

    container.add_item(ui.TextDisplay("**Ticket作成時にメンションするロール**"))
    row2 = ui.ActionRow()
    default_values = await self.get_fetch_role(guild, self.data[guild.id]["ticket_mention_role_id"])
    row2.add_item(ui.RoleSelect(
      placeholder="ロールを選択（任意）",
      custom_id=f"settings_ticket_mention_role",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row2)

    container.add_item(ui.TextDisplay("**Ticket作成用ボタンを設置するチャンネル**"))
    row3 = ui.ActionRow()
    default_values = await self.get_fetch_channel(guild, self.data[guild.id]["ticket_button_channel_id"])
    row3.add_item(ui.ChannelSelect(
      placeholder="チャンネルを選択（任意）",
      channel_types=[discord.ChannelType.text],
      custom_id=f"settings_ticket_button_channel",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row3)

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    row3 = ui.ActionRow()
    row3.add_item(ui.Button(label="戻る", emoji=EMOJI_DICT["arrow_back"], custom_id=f"settings_page_2", style=discord.ButtonStyle.gray, row=0))
    row3.add_item(ui.Button(label="Ticket作成ボタンを設置せずに終了", emoji=EMOJI_DICT["check"], custom_id=f"settings_page_4_no", style=discord.ButtonStyle.gray, row=1))
    row3.add_item(ui.Button(label="Ticket作成ボタンを設置して終了", emoji=EMOJI_DICT["new_label"], custom_id=f"settings_page_4_yes", style=discord.ButtonStyle.gray, row=2))
    container.add_item(row3)

    view = ui.LayoutView()
    view.add_item(container)

    await interaction.response.edit_message(view=view)


  async def settings_page_4(self, interaction:discord.Interaction, custom_id: str):
    guild = interaction.guild
    if not guild:
      return

    if "yes" in custom_id:
      url = await self.send_ticket_button(guild)
      msg = f"**Ticket作成ボタン**\n{url}"
    else:
      msg = None

    container = ui.Container(accent_color=0xc8e1ff)
    container.add_item(ui.TextDisplay("**settings**"))

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    container.add_item(ui.TextDisplay("### 設定が完了しました"))
    if msg:
      container.add_item(ui.Separator())
      container.add_item(ui.TextDisplay(msg))

    view = ui.LayoutView()
    view.add_item(container)

    await interaction.response.edit_message(view=view)


  async def send_ticket_button(self, guild: discord.Guild) -> str:
    ticket_button_channel_id = self.data[guild.id]["ticket_button_channel_id"]
    ticket_button_channel = (await self.get_fetch_channel(guild, ticket_button_channel_id))[0]

    embed = discord.Embed(
      description="## 匿名Ticket\n匿名Ticketを作成します。\nこのbotのDMを通じて匿名でサーバー管理者と会話することができます。",
      color=0xc8e1ff
    )

    view = ui.View()
    view.add_item(ui.Button(label="匿名Ticket", emoji=EMOJI_DICT["new_label"], custom_id=f"private_ticket", style=discord.ButtonStyle.gray))

    msg = await ticket_button_channel.send(embed=embed, view=view)
    return msg.jump_url


  async def get_fetch_channel(self, guild: discord.Guild, channel_id: int | None) -> list[discord.TextChannel]:
    if not channel_id:
      return []

    channel = guild.get_channel(channel_id)
    if not channel:
      try:
        channel = await guild.fetch_channel(channel_id)
      except Exception:
        return []

    if not isinstance(channel, discord.TextChannel):
      return []

    my_permission = channel.permissions_for(guild.me)
    if not all([my_permission.read_messages, my_permission.send_messages, my_permission.create_public_threads]):
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
    guild = interaction.guild
    if not guild:
      return

    if not interaction.data:
      return

    custom_id = interaction.data.get("custom_id")
    if not custom_id:
      return

    # page
    if "settings_page" in custom_id:
      if custom_id == "settings_page_1":
        view = self.settings_page_1()
        await interaction.response.edit_message(view=view)
        return

      elif custom_id == "settings_page_2":
        await self.settings_page_2(interaction)
        return

      elif custom_id == "settings_page_3":
        await self.settings_page_3(interaction)
        return

      elif "settings_page_4" in custom_id:
        await self.settings_page_4(interaction, custom_id)
        return

    # settings
    if "settings_report" in custom_id or "settings_ticket" in custom_id:
      values = interaction.data.get("values")

      case_type = "report" if "report" in custom_id else "ticket"
      value = int(values[0]) if values else None

      if "button_channel" in custom_id:
        self.data[guild.id]["ticket_button_channel_id"] = value

      elif "channel" in custom_id:
        self.data[guild.id][str(f"{case_type}_channel_id")] = value

      elif "mention_role" in custom_id:
        self.data[guild.id][str(f"{case_type}_mention_role_id")] = value


      if case_type == "report":
        await self.settings_page_2(interaction)
      else:
        await self.settings_page_3(interaction)


      await self.db.upsert_guild_settings(self.data[guild.id])
      return






async def setup(bot):
  await bot.add_cog(Settings(bot))