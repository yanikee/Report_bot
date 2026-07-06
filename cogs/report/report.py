from discord import (
  ButtonStyle,
  Embed,
  Interaction,
  Member,
  Message,
  SeparatorSpacing,
  TextChannel,
  TextStyle,
  User,
  app_commands,
  ui,
)
from discord.ext import commands

from bot import ReportBot
from const import EMOJI_DICT
from modules import error, functions
from modules.db import DB


class Report(commands.Cog):
  def __init__(self, bot: ReportBot):
    self.bot = bot
    self.db = DB()
    self.user_cooldowns = {}
    self.ctx_menu = app_commands.ContextMenu(
      name="!【サーバー管理者に報告】",
      callback=self.report,
    )
    self.bot.tree.add_command(self.ctx_menu)

  async def cog_unload(self):
    self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

  async def report(self, interaction: Interaction, message: Message):
    guild_id, channel_id = (interaction.guild_id, interaction.channel_id)
    if not guild_id or not channel_id:
      msg = "サーバーで実行してください"
      await error.send_error(msg, interaction)
      return

    await interaction.response.defer(ephemeral=True)

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

    report_channel_id = guild_data["report_channel_id"]
    if not report_channel_id:
      msg = "`/settings`を実行してください"
      await error.send_error(msg, interaction, followup=True)
      return

    embed, self.user_cooldowns = functions.user_cooldown(interaction.user.id, self.user_cooldowns)
    if embed:
      await interaction.followup.send(embed=embed)
      return

    view = ReportButton(self.bot, interaction, message)

    await interaction.followup.send(view=view)



class ReportButton(ui.LayoutView):
  def __init__(self, bot: ReportBot, interaction: Interaction, message: Message, timeout=30):
    super().__init__(timeout=timeout)
    self.bot = bot
    self.db = DB()
    self.interaction = interaction
    self.message = message

    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("## Report"))
    container.add_item(ui.TextDisplay("**通常報告**：報告者名がサーバー管理者に伝わる\n**匿名報告**：報告者名は誰にも伝わらない"))

    row = ui.ActionRow()
    self.button_0 = ui.Button(label='通常報告', emoji=EMOJI_DICT["person_alert"], custom_id='public_report', style=ButtonStyle.gray)
    self.button_1 = ui.Button(label='匿名報告', emoji=EMOJI_DICT["report"], custom_id='private_report', style=ButtonStyle.gray)
    row.add_item(self.button_0)
    row.add_item(self.button_1)

    container.add_item(row)

    self.add_item(container)


  async def interaction_check(self, interaction: Interaction) -> bool:
    if not interaction.data:
      return False

    custom_id = interaction.data.get("custom_id")
    if not custom_id:
      return False

    if custom_id == "public_report":
      await self.do_report(interaction, self.message, reporter=interaction.user)
      return True

    elif custom_id == "private_report":
      # 後ほどDMを使うため、初めにDMにメッセージを送れるか試す
      try:
        await interaction.user.send("テストメッセージ", delete_after=0.1)
      except Exception:
        msg = "botからあなたのDMにメッセージを送信できませんでした\n設定を確認してください"
        await error.send_error(msg, interaction)
        return False

      await self.do_report(interaction, self.message, reporter=None)
      return True

    return False


  async def do_report(self, interaction: Interaction, message: Message, reporter: User | Member | None):
    embed = Embed(
      description=f"{message.content}\n{message.jump_url}",
      color=0xffe7ab,
    )
    embed.set_image(url=message.attachments[0].url if message.attachments else None)
    embed.set_author(
      name=f"投稿者：{message.author.display_name}",
      icon_url=message.author.display_avatar.url if message.author.display_avatar else None
    )
    embed.set_footer(
      text=f"報告者：{reporter.display_name}" if reporter else "報告者：匿名",
      icon_url=reporter.display_avatar.url if reporter else None,
    )
    message.embeds.insert(0, embed)

    guild_id = interaction.guild_id
    if not guild_id:
      return

    guild_data = await self.db.get_guild_settings(guild_id)
    if not guild_data:
      return

    report_channel_id = guild_data["report_channel_id"]
    if not report_channel_id:
      return

    channel = self.bot.get_channel(report_channel_id)
    if not channel:
      try:
        channel = await self.bot.fetch_channel(report_channel_id)
      except Exception:
        msg = "チャンネルを取得できませんでした\n`/settings`を再実行してください"
        await error.send_error(msg, interaction)
        return

    if not isinstance(channel, TextChannel):
      return

    report_menntion_role_id = guild_data["report_mention_role_id"]

    if report_menntion_role_id:
      mention_msg = f"<@&{report_menntion_role_id}>"
    else:
      mention_msg = None

    try:
      report_msg = await channel.send(mention_msg, embeds=message.embeds)
    except Exception:
      msg = "レポートを送信できませんでした\n`/settings`を再実行してください"
      await error.send_error(msg, interaction)
      return

    modal = ReportReasonModal(interaction, message, report_msg, reporter)
    await interaction.response.send_modal(modal)

    if not reporter:
      await self.db.create_thread_entry(
        thread_id=report_msg.id,
        guild_id=guild_id,
        user_id=interaction.user.id,
        case_type="report"
      )

      view = ui.View()
      button_0 = ui.Button(label="返信", emoji=EMOJI_DICT["reply"], custom_id="report_create_thread", style=ButtonStyle.gray)
      view.add_item(button_0)

      await report_msg.edit(view=view)



class ReportReasonModal(ui.Modal):
  def __init__(self, interaction: Interaction, reported_msg: Message, report_msg: Message, reporter: User | Member | None):
    super().__init__(title='匿名Report')
    self.interaction = interaction
    self.reported_msg = reported_msg
    self.reporter = reporter
    self.report_msg = report_msg

    self.report_reason = ui.TextInput(
      label="Report理由",
      style=TextStyle.long,
      required=True,
      row=0
    )
    self.add_item(self.report_reason)

  async def on_submit(self, interaction: Interaction):
    guild = interaction.guild
    if not guild:
      return

    embed = Embed(
      title="報告の理由",
      description=self.report_reason.value,
      color=0xffe7ab,
    )
    embed.set_footer(
      text=f"報告者：{self.reporter.display_name}" if self.reporter else "報告者：匿名",
      icon_url=self.reporter.display_avatar.url if self.reporter else None,
    )
    embeds = self.report_msg.embeds or []
    embeds.append(embed)
    await self.report_msg.edit(embeds=embeds)

    if not self.interaction.message:
      return

    await interaction.response.defer()

    view = ui.LayoutView()
    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("## Report"))

    if self.reporter:
      msg = "報告が完了しました\nサーバー管理者から直接話を伺うことがあります"
    else:
      msg = "サーバー管理者に匿名Reportが送信されました\nDMにてサーバー管理者と会話を行うことができます"

    msg += f"\n\n**報告したメッセージ**\n{self.reported_msg.jump_url}"

    container.add_item(ui.TextDisplay(msg))
    view.add_item(container)
    await self.interaction.followup.edit_message(self.interaction.message.id, view=view)

    if not self.reporter:
      view = ui.LayoutView()
      container = ui.Container(accent_color=0xffe7ab)

      icon_url = guild.icon.url if guild.icon else "https://example.com"

      thumbnail = ui.Thumbnail(icon_url, description=f"{guild.id}/{self.report_msg.channel.id}/{self.report_msg.id}")
      section = ui.Section(accessory=thumbnail)
      section.add_item(ui.TextDisplay("# 匿名Report"))
      section.add_item(ui.TextDisplay("- ファイル添付や追伸の際には、__**このメッセージに返信**__してください"))
      container.add_item(section)

      container.add_item(ui.Separator())
      container.add_item(ui.TextDisplay(f"## Reportしたメッセージ\n　{self.reported_msg.jump_url}"))
      container.add_item(ui.TextDisplay(f"## Report理由\n{self.report_reason.value}"))

      container.add_item(ui.Separator(spacing=SeparatorSpacing.large))

      container.add_item(ui.TextDisplay(f"匿名Report | {guild.name}", id=998))

      view.add_item(container)

      await interaction.user.send(view=view)



async def setup(bot):
  await bot.add_cog(Report(bot))
