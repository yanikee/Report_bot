from discord.ext import commands
from discord import app_commands, ui
import discord

from modules import error, functions
from modules.db import DB, GuildSettings
from modules.functions import create_reply_view
from const import EMOJI_DICT



class PrivateTicket(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.db = DB()
    self.user_cooldowns = {}

  @commands.Cog.listener()
  async def on_interaction(self, interaction: discord.Interaction):
    if not interaction.data:
      return

    custom_id = interaction.data.get("custom_id", "")

    if custom_id != "private_ticket":
      return

    guild_id, channel_id = (interaction.guild_id, interaction.channel_id)
    if not guild_id or not channel_id:
      msg = "サーバーで実行してください"
      await error.send_error(msg, interaction)
      return

    guild_data = await self.db.get_guild_settings(guild_id)
    if not guild_data:
      msg = "サーバーデータが見つかりませんでした\n`/settings`を実行してください"
      await error.send_error(msg, interaction, followup=True)
      return

    is_guild_blocked = await self.db.is_guild_blocked(guild_id, interaction.user.id)
    if is_guild_blocked:
      msg = "サーバーブロックされています"
      await error.send_error(msg, interaction, followup=True)
      return

    ticket_channel_id = guild_data["ticket_channel_id"]
    if not ticket_channel_id:
      msg = "`/settings`を実行してください"
      await error.send_error(msg, interaction, followup=True)
      return

    embed, self.user_cooldowns = functions.user_cooldown(interaction.user.id, self.user_cooldowns)
    if embed:
      await interaction.followup.send(embed=embed)
      return

    modal = PrivateTicketModal(self.bot)
    await interaction.response.send_modal(modal)


class PrivateTicketModal(ui.Modal):
  def __init__(self, bot: commands.Bot):
    super().__init__(title=f'匿名Ticketモーダル')
    self.bot = bot
    self.db = DB()

    self.pticket_input = ui.TextInput(
      style=discord.TextStyle.long,
      default=None,
      required=True,
    )
    self.file_input = ui.FileUpload(
      required=False,
      max_values=3
    )
    self.add_item(ui.Label(text="Ticket内容", component=self.pticket_input))
    self.add_item(ui.Label(text="添付ファイル", component=self.file_input))


  async def on_submit(self, interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)

    guild = interaction.guild
    if not guild:
      return

    guild_data = await self.db.get_guild_settings(guild.id)
    if not guild_data:
      return

    ticket_channel_id = guild_data["ticket_channel_id"]
    if not ticket_channel_id:
      return

    channel = self.bot.get_channel(ticket_channel_id)
    if not channel:
      try:
        channel = await self.bot.fetch_channel(ticket_channel_id)
      except Exception:
        msg = "チャンネルを取得できませんでした\n`/settings`を再実行してください"
        await error.send_error(msg, interaction, followup=True)
        return

    if not isinstance(channel, discord.TextChannel):
      return


    view = ui.LayoutView()

    ticket_mention_role_id = guild_data["ticket_mention_role_id"]
    if ticket_mention_role_id:
      container = ui.Container()
      container.add_item(ui.TextDisplay(f"<@&{ticket_mention_role_id}>"))
      view.add_item(container)

    container = ui.Container(accent_color=0xc8e1ff)
    container.add_item(ui.TextDisplay("## 匿名Ticket"))
    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay(f"## Ticket内容\n{self.pticket_input.value}"))

    if attachments := self.file_input.values:
      container.add_item(ui.TextDisplay("## 添付ファイル"))
      for attachment in attachments:
        file = await attachment.to_file()
        container.add_item(ui.File(media=file))

    view.add_item(container)

    container = ui.Container()
    row = ui.ActionRow()
    row.add_item(ui.Button(label="返信", emoji=EMOJI_DICT["reply"], custom_id=f"pticket_create_thread", style=discord.ButtonStyle.gray))
    container.add_item(row)
    view.add_item(container)


    try:
      pticket_msg = await channel.send(view=view)
    except Exception:
      msg = "匿名Ticketを送信できませんでした"
      await error.send_error(msg, interaction)
      return

    await self.db.create_thread_entry(
      thread_id=pticket_msg.id,
      guild_id=guild.id,
      user_id=interaction.user.id,
      case_type="ticket"
    )

    view = ui.LayoutView()
    container = ui.Container(accent_color=0xc8e1ff)

    icon_url = guild.icon.url if guild.icon else "https://example.com"

    thumbnail = ui.Thumbnail(icon_url, description=f"{guild.id}/{pticket_msg.channel.id}/{pticket_msg.id}")
    section = ui.Section(accessory=thumbnail)
    section.add_item(ui.TextDisplay("# 匿名Ticket"))
    section.add_item(ui.TextDisplay("- ファイル添付や追伸の際には、__**このメッセージに返信**__してください。"))
    container.add_item(section)

    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay(f"## Ticket内容\n{self.pticket_input.value}"))

    if attachments := self.file_input.values:
      container.add_item(ui.TextDisplay("## 添付ファイル"))
      for attachment in attachments:
        file = await attachment.to_file()
        container.add_item(ui.File(media=file))

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    container.add_item(ui.TextDisplay(f"匿名Ticket｜{guild.name}", id=998))

    view.add_item(container)

    await interaction.user.send(view=view)

    await interaction.followup.send("匿名Ticketが完了しました\nDMにてサーバー管理者と会話を行うことができます")



async def setup(bot):
  await bot.add_cog(PrivateTicket(bot))
