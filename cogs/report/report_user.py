from discord.ext import commands
from discord import ui, components
import discord

import re

from modules.functions import user_cooldown, create_reply_view
from modules.db import DB
from modules import error



class ReportUser(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.db = DB()
    self.user_cooldowns = {}

  @commands.Cog.listener()
  async def on_message(self, message: discord.Message):
    if not isinstance(message.channel, discord.DMChannel):
      return

    if message.author.bot:
      return

    reference = message.reference

    if message.type != discord.MessageType.reply or not reference:
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

      if not "匿名Report | " in content:
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
        if not "------------返信内容------------" in description:
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

    is_guild_blocked = await self.db.is_guild_blocked(guild_id, user_id)
    if is_guild_blocked:
      return

    if thread_data["is_blocked"]:
      return

    embed, self.user_cooldowns = user_cooldown(user_id, self.user_cooldowns)
    if embed:
      await message.add_reaction("❌")
      embed.set_footer(text="このメッセージは15秒後に削除されます。")
      await message.reply(embed=embed, delete_after=15)
      return

    channel = self.bot.get_channel(channel_id)
    if not channel:
      try:
        channel = await self.bot.fetch_channel(channel_id)
      except Exception:
        msg = "チャンネルが存在しませんでした\nサーバーで`/settings`を実行してください"
        await error.send_error(msg, channel=message.channel)
        return

    if not isinstance(channel, discord.TextChannel):
      return

    try:
      report_msg = await channel.fetch_message(message_id)
    except Exception:
      msg = "スレッドが取得できませんでした"
      await error.send_error(msg, channel=message.channel)
      return

    report_thread = report_msg.thread

    if not report_thread:
      guild_data["report_count"] += 1
      name = f"private_report-{str(guild_data["report_count"]).zfill(4)}"

      try:
        report_thread = await report_msg.create_thread(name=name)
      except Exception:
        msg = "スレッドが作成できませんでした"
        await error.send_error(msg, channel=message.channel)
        return

    await report_msg.edit(view=None)

    # アーカイブされていた場合、親チャンネルに通知
    if report_thread.archived:
      embed=discord.Embed(
        title="お知らせ",
        description=f"{report_thread.mention}に、新しい返信が届きました。",
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
    except Exception:
      msg = "スレッドにメッセージを送信できませんでした"
      await error.send_error(msg, channel=message.channel)
      return


    if panel_msg:
      view = ui.LayoutView().from_message(panel_msg)

    else:
      view, _ = await create_reply_view("report")

    try:
      await report_thread.send(view=view)
    except Exception:
      await message.add_reaction("✖")
      return

    await message.add_reaction("✅")



async def setup(bot):
  await bot.add_cog(ReportUser(bot))