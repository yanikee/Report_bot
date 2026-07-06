from discord import (
  ButtonStyle,
  ChannelType,
  Embed,
  Guild,
  Interaction,
  Role,
  SeparatorSpacing,
  TextChannel,
  TextStyle,
  app_commands,
  ui,
)
from discord.ext import commands

from bot import ReportBot
from const import EMOJI_DICT
from modules.db import DB, GuildSettings
from modules.error import send_error


class Settings(commands.Cog):
  def __init__(self, bot: ReportBot):
    self.bot = bot
    self.db = DB()
    self.data: dict[int, GuildSettings] = {}


  @app_commands.command(name="settings", description='設定を行います')
  @app_commands.guild_only()
  async def settings(self, interaction: Interaction):
    guild = interaction.guild
    if not guild:
      return

    await interaction.response.defer(ephemeral=True)

    guild_data = await self.db.get_guild_settings(guild.id)
    if not guild_data:
      guild_data = await self.db.create_guild_settings(guild.id)

    self.data[guild.id] = guild_data

    view = self.get_settings_page_1()
    await interaction.followup.send(view=view)


  def get_settings_page_1(self) -> ui.LayoutView:
    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("**settings (1/3)**\n"
                                      "1. Report機能\n"
                                      "1. Ticket機能\n"
                                      "これらの設定を行います"))
    row = ui.ActionRow()
    row.add_item(ui.Button(label="次へ", emoji=EMOJI_DICT["arrow_forward"], custom_id="settings_page_2", style=ButtonStyle.gray))
    container.add_item(row)

    view = ui.LayoutView()
    view.add_item(container)
    return view


  async def get_settings_page_2(self, interaction: Interaction) -> ui.LayoutView | None:
    guild = interaction.guild
    if not guild:
      return

    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("**settings (2/3)**\n## Report機能の設定"))

    container.add_item(ui.Separator(spacing=SeparatorSpacing.large))

    container.add_item(ui.TextDisplay("**Reportを作成するチャンネル**"))
    row1 = ui.ActionRow()
    default_values = await self.get_fetch_channels(interaction, guild, self.data[guild.id]["report_channel_id"])
    row1.add_item(ui.ChannelSelect(
      placeholder="チャンネルを選択（任意）",
      channel_types=[ChannelType.text],
      custom_id="settings_report_channel",
      min_values=0,
      default_values=default_values if default_values else []
    ))
    container.add_item(row1)

    container.add_item(ui.TextDisplay("**Report作成時にメンションするロール**"))
    row2 = ui.ActionRow()
    default_values = await self.get_fetch_roles(guild, self.data[guild.id]["report_mention_role_id"])
    row2.add_item(ui.RoleSelect(
      placeholder="ロールを選択（任意）",
      custom_id="settings_report_mention_role",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row2)

    container.add_item(ui.Separator(spacing=SeparatorSpacing.large))

    row3 = ui.ActionRow()
    row3.add_item(ui.Button(label="戻る", emoji=EMOJI_DICT["arrow_back"], custom_id="settings_page_1", style=ButtonStyle.gray))
    row3.add_item(ui.Button(label="次へ", emoji=EMOJI_DICT["arrow_forward"], custom_id="settings_page_3", style=ButtonStyle.gray))
    container.add_item(row3)

    view = ui.LayoutView()
    view.add_item(container)

    return view


  async def get_settings_page_3(self, interaction: Interaction) -> ui.LayoutView | None:
    guild = interaction.guild
    if not guild:
      return

    container = ui.Container(accent_color=0xc8e1ff)
    container.add_item(ui.TextDisplay("**settings (3/3)**\n## Ticket機能の設定"))

    container.add_item(ui.Separator(spacing=SeparatorSpacing.large))

    container.add_item(ui.TextDisplay("**Tiekctを作成するチャンネル**"))
    row1 = ui.ActionRow()
    default_values = await self.get_fetch_channels(interaction, guild, self.data[guild.id]["ticket_channel_id"])
    row1.add_item(ui.ChannelSelect(
      placeholder="チャンネルを選択（任意）",
      channel_types=[ChannelType.text],
      custom_id="settings_ticket_channel",
      min_values=0,
      default_values=default_values if default_values else []
    ))
    container.add_item(row1)

    container.add_item(ui.TextDisplay("**Ticket作成時にメンションするロール**"))
    row2 = ui.ActionRow()
    default_values = await self.get_fetch_roles(guild, self.data[guild.id]["ticket_mention_role_id"])
    row2.add_item(ui.RoleSelect(
      placeholder="ロールを選択（任意）",
      custom_id="settings_ticket_mention_role",
      min_values=0,
      default_values=default_values
    ))
    container.add_item(row2)

    container.add_item(ui.TextDisplay("**Ticket作成用ボタンを設置するチャンネル**"))
    row3 = ui.ActionRow()
    default_values = await self.get_fetch_channels(interaction, guild, self.data[guild.id]["ticket_button_channel_id"])
    row3.add_item(ui.ChannelSelect(
      placeholder="チャンネルを選択（任意）",
      channel_types=[ChannelType.text],
      custom_id="settings_ticket_button_channel",
      min_values=0,
      default_values=default_values if default_values else []
    ))
    container.add_item(row3)

    container.add_item(ui.Separator(spacing=SeparatorSpacing.large))

    row3 = ui.ActionRow()
    row3.add_item(ui.Button(label="戻る", emoji=EMOJI_DICT["arrow_back"], custom_id="settings_page_2", style=ButtonStyle.gray, row=0))
    row3.add_item(ui.Button(label="Ticket作成ボタンを設置せずに終了", emoji=EMOJI_DICT["check"], custom_id="settings_page_4_no", style=ButtonStyle.gray, row=1))
    disable = not all([self.data[guild.id]["ticket_channel_id"], self.data[guild.id]["ticket_button_channel_id"]])
    row3.add_item(ui.Button(label="Ticket作成ボタンを設置して終了", emoji=EMOJI_DICT["new_label"], custom_id="settings_page_4_yes", style=ButtonStyle.gray, row=2, disabled=disable))
    container.add_item(row3)

    view = ui.LayoutView()
    view.add_item(container)

    return view


  async def get_settings_page_4(self, interaction: Interaction, custom_id: str) -> ui.LayoutView | None:
    guild = interaction.guild
    if not guild:
      return

    if "yes" in custom_id:
      ticket_button_channel_id = self.data[guild.id]["ticket_button_channel_id"]
      await self.send_ticket_button(interaction, guild, ticket_button_channel_id)
      msg = f"**Ticket作成ボタン**\n<#{ticket_button_channel_id}>"
    else:
      await interaction.response.defer()
      msg = None

    container = ui.Container(accent_color=0xc8e1ff)
    container.add_item(ui.TextDisplay("**settings**"))

    container.add_item(ui.Separator(spacing=SeparatorSpacing.large))

    container.add_item(ui.TextDisplay("### 設定が完了しました"))
    if msg:
      container.add_item(ui.Separator())
      container.add_item(ui.TextDisplay(msg))

    view = ui.LayoutView()
    view.add_item(container)

    return view


  async def send_ticket_button(self, interaction: Interaction, guild: Guild, ticket_button_channel_id: int | None) -> None:
    ticket_button_channel = await self.get_fetch_channels(interaction, guild, ticket_button_channel_id)

    if not ticket_button_channel:
      return

    modal = EditTicketButtonModal(self.bot, ticket_button_channel[0])
    await interaction.response.send_modal(modal)

    return


  async def get_fetch_channels(self, interaction: Interaction, guild: Guild, channel_id: int | None) -> list[TextChannel] | None:
    if not channel_id:
      return []

    channel = guild.get_channel(channel_id)
    if not channel:
      try:
        channel = await guild.fetch_channel(channel_id)
      except Exception:
        msg = f"<#{channel_id}>\nこのチャンネルは選択できません\nbotに正しい権限があるか確認してください"
        await send_error(msg, interaction=interaction)
        return None

    if not isinstance(channel, TextChannel):
      return None

    my_permission = channel.permissions_for(guild.me)
    if not all([my_permission.read_messages, my_permission.send_messages, my_permission.create_public_threads]):
      msg = f"<#{channel_id}>\nこのチャンネルは選択できません\nbotに正しい権限があるか確認してください"
      await send_error(msg, interaction=interaction, followup=True)
      return None

    return [channel]

  async def get_fetch_roles(self, guild: Guild, role_id: int | None) -> list[Role]:
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
  async def on_interaction(self, interaction: Interaction):
    guild = interaction.guild
    if not guild:
      return

    message = interaction.message
    if not message:
      return

    message_id = message.id

    if not interaction.data:
      return

    custom_id = interaction.data.get("custom_id")
    if not custom_id:
      return

    # page
    if "settings_page" in custom_id:
      if custom_id == "settings_page_1":
        await interaction.response.defer()
        view = self.get_settings_page_1()

      elif custom_id == "settings_page_2":
        await interaction.response.defer()
        view = await self.get_settings_page_2(interaction)

      elif custom_id == "settings_page_3":
        await interaction.response.defer()
        view = await self.get_settings_page_3(interaction)

      elif "settings_page_4" in custom_id:
        view = await self.get_settings_page_4(interaction, custom_id)

      else:
        return

      await interaction.followup.edit_message(message_id, view=view)
      return


    # settings
    if "settings_report" in custom_id or "settings_ticket" in custom_id:
      await interaction.response.defer()

      values = interaction.data.get("values")

      case_type = "report" if "report" in custom_id else "ticket"
      value = int(values[0]) if values else None

      if "mention_role" in custom_id:
        self.data[guild.id][str(f"{case_type}_mention_role_id")] = value

      if "channel" in custom_id:
        channel = await self.get_fetch_channels(interaction, guild, value)

        if channel is not None:
          if "button_channel" in custom_id:
            self.data[guild.id]["ticket_button_channel_id"] = value

          elif "channel" in custom_id:
            self.data[guild.id][str(f"{case_type}_channel_id")] = value


      if case_type == "report":
        view = await self.get_settings_page_2(interaction)
      else:
        view = await self.get_settings_page_3(interaction)

      await interaction.followup.edit_message(message_id, view=view)

      await self.db.upsert_guild_settings(self.data[guild.id])
      return


class EditTicketButtonModal(ui.Modal):
  def __init__(self, bot: ReportBot, channel: TextChannel):
    super().__init__(title="チケット編集モーダル")
    self.bot = bot
    self.channel = channel

    self.text_input = ui.TextInput(
      style=TextStyle.long,
      default="## 匿名Ticket\n匿名Ticketを作成します\nこのbotのDMを通じて匿名でサーバー管理者と会話することができます"
    )
    self.add_item(ui.Label(text="チケットを開始するボタンのメッセージ", component=self.text_input))

  async def on_submit(self, interaction: Interaction):
    await interaction.response.defer()

    embed = Embed(
      description=self.text_input.value,
      color=0xc8e1ff
    )

    view = ui.View()
    view.add_item(ui.Button(label="匿名Ticket", emoji=EMOJI_DICT["new_label"], custom_id="private_ticket", style=ButtonStyle.gray))

    await self.channel.send(embed=embed, view=view)


async def setup(bot):
  await bot.add_cog(Settings(bot))
