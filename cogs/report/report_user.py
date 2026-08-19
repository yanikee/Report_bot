import re

from discord import DMChannel, Embed, Message, MessageType, components, ui
from discord.ext import commands

from bot import ReportBot
from modules import error
from modules.functions import (
  create_reply_view,
  raise_on_guild_block,
  resolve_text_channel,
  user_cooldown,
)


class ReportUser(commands.Cog):
  def __init__(self, bot: ReportBot):
    self.bot = bot
    self.db = bot.db
    self.user_cooldowns = {}

  @commands.Cog.listener()
  async def on_message(self, message: Message):
    if not isinstance(message.channel, DMChannel):
      return

    if message.author.bot:
      return

    reference = message.reference

    if message.type != MessageType.reply or not reference:
      return

    msg = reference.cached_message
    if not msg:
      msg_id = reference.message_id
      if not msg_id:
        return
      try:
        msg = await message.channel.fetch_message(msg_id)
      except Exception:
        return

    if not msg.embeds:
      target_id = 998
      content = next((
        child.content
        for comp in msg.components if isinstance(comp, components.Container)
        for child in comp.children
        if isinstance(child, components.TextDisplay) and child.id == target_id
      ), "")

      if "匿名Report | " not in content:
        return

      description = next((
        child.accessory.description
        for comp in msg.components if isinstance(comp, components.Container)
        for child in comp.children if isinstance(child, components.SectionComponent)
        if isinstance(child.accessory, components.ThumbnailComponent)
      ), None)

      if not description:
        return

      guild_id, channel_id, message_id = [int(x) for x in description.split("/")]


    else:
      embed = msg.embeds[0]
      description = embed.description
      footer_text = embed.footer.text

      if footer_text:
        if "匿名報告 |" not in footer_text and "匿名Report |" not in footer_text:
          return

      else:
        if not description:
          return
        if "------------返信内容------------" not in description:
          return

      report_msg_url = embed.url
      if not report_msg_url:
        return

      match = re.search(r'channels/(\d+)/(\d+)/(\d+)', report_msg_url)
      if not match:
        return None

      guild_id = int(match.group(1))
      channel_id = int(match.group(2))
      message_id = int(match.group(3))


    guild_data = await self.db.get_guild_settings(guild_id)
    if not guild_data:
      msg = "サーバーデータが存在しません\nサーバーで`/settings`を実行してください"
      await error.send_error(msg, channel=message.channel)
      return

    thread_data = await self.db.get_thread(message_id)
    if not thread_data:
      msg = "スレッドデータが存在しませんでした"
      await error.send_error(msg, channel=message.channel)
      return

    user_id = message.author.id

    if thread_data["user_id"] != user_id:
      msg = "この操作は行えません"
      await error.send_error(msg, channel=message.channel)
      return

    if await raise_on_guild_block(self.db, guild_id, user_id, channel=message.channel):
      return

    if thread_data["is_blocked"]:
      msg = "ブロックされています"
      await error.send_error(msg, channel=message.channel)
      return

    embed = user_cooldown(user_id, self.user_cooldowns)
    if embed:
      await message.add_reaction("❌")
      embed.set_footer(text="このメッセージは15秒後に削除されます")
      await message.reply(embed=embed, delete_after=15)
      return

    channel = await resolve_text_channel(self.bot, channel_id)
    if not channel:
      msg = "チャンネルが存在しませんでした\nサーバーで`/settings`を実行してください"
      await error.send_error(msg, channel=message.channel)
      return

    try:
      report_msg = await channel.fetch_message(message_id)
    except Exception as e:
      self.bot.log(f"メッセージ取得に失敗: {e}", "ERROR")
      msg = "スレッドが取得できませんでした"
      await error.send_error(msg, channel=message.channel)
      return

    report_thread = report_msg.thread

    if not report_thread:
      guild_data["report_count"] += 1
      name = f"private_report-{str(guild_data["report_count"]).zfill(4)}"

      try:
        report_thread = await report_msg.create_thread(name=name)
      except Exception as e:
        self.bot.log(f"スレッド作成に失敗: {e}", "ERROR")
        msg = "スレッドが作成できませんでした"
        await error.send_error(msg, channel=message.channel)
        return

      await self.db.upsert_guild_settings(guild_data)

    await report_msg.edit(view=None)

    # アーカイブされていた場合、親チャンネルに通知
    if report_thread.archived:
      embed = Embed(
        title="お知らせ",
        description=f"{report_thread.mention}に、新しい返信が届きました",
        color=0xff33ff,
      )
      embed.set_footer(text="スレッドがアーカイブされていたため通知されました")
      await channel.send(embed=embed)

    panel_msg = None
    async for msg in report_thread.history(limit=5):
      if msg.components:
        panel_msg = msg
        await msg.delete()
        break


    view = ui.LayoutView()

    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("## Report"))
    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay(f"## ユーザーからの返信\n{message.content}"))

    files = []
    if attachments := message.attachments:
      container.add_item(ui.TextDisplay("## 添付ファイル"))
      for attachment in attachments:
        file_data = await attachment.to_file()
        files.append(file_data)
        container.add_item(ui.File(media=file_data))

    view.add_item(container)

    try:
      await report_thread.send(view=view, files=files)
    except Exception as e:
      self.bot.log(f"スレッドへの送信に失敗: {e}", "ERROR")
      msg = "スレッドにメッセージを送信できませんでした"
      await error.send_error(msg, channel=message.channel)
      return


    if panel_msg:
      view = ui.LayoutView().from_message(panel_msg)

    else:
      view, _ = await create_reply_view("report")

    try:
      await report_thread.send(view=view)
    except Exception as e:
      self.bot.log(f"スレッドへの送信に失敗: {e}", "ERROR")
      await message.add_reaction("✖")
      return

    await message.add_reaction("✅")



async def setup(bot):
  await bot.add_cog(ReportUser(bot))
