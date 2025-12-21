from discord.ext import commands
from discord import ui
import discord

import re

from modules import check
from modules.db import DB
from const import EMOJI_DICT



class ReplyToReply(commands.Cog):
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
      return

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
      return

    thread_data = await self.db.get_thread(message_id)
    if not thread_data:
      return

    user_id = message.author.id

    is_guild_blocked = await self.db.is_guild_blocked(guild_id, user_id)
    if is_guild_blocked:
      return

    if thread_data["is_blocked"]:
      return

    # cooldown
    embed, self.user_cooldowns = check.user_cooldown(user_id, self.user_cooldowns)
    if embed:
      await message.add_reaction("❌")
      embed.set_footer(text="このメッセージは15秒後に削除されます。")
      await message.reply(embed=embed, delete_after=15)
      return

    # threadを取得
    channel = self.bot.get_channel(channel_id)
    if not channel:
      try:
        channel = await self.bot.fetch_channel(channel_id)
      except Exception:
        return

    if not isinstance(channel, discord.TextChannel):
      return

    try:
      report_msg = await channel.fetch_message(message_id)
    except Exception:
      return

    report_thread = report_msg.thread

    if not report_thread:
      guild_data["report_count"] += 1
      name = f"private_report-{str(guild_data["report_count"]).zfill(4)}"

      try:
        report_thread = await report_msg.create_thread(name=name)
      except Exception:
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

    # embedの定義
    embed=discord.Embed(
      title="ユーザーからの返信",
      description=message.content,
      color=0xffe7ab,
    )

    # ユーザーからの返信を送信
    try:
      await report_thread.send(embed=embed)
    except Exception:
      return

    # 返信ボタンが設置されてたら削除
    async for msg in report_thread.history(limit=5):
      if msg.components:
        await msg.delete()
        break

    view = ui.LayoutView()

    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("## Report"))

    container.add_item(ui.Separator())

    container.add_item(ui.TextDisplay(f"### 返信内容\n下のボタンから編集してください。"))

    container.add_item(ui.TextDisplay(f"### 添付ファイル"))
    if attachments := message.attachments:
      for attachment in attachments:
        container.add_item(ui.File(await attachment.to_file()))
    else:
      container.add_item(ui.TextDisplay("なし"))

    view.add_item(container)
    view.add_item(ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"report_edit_reply", style=discord.ButtonStyle.primary))
    view.add_item(ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"report_send", style=discord.ButtonStyle.red, disabled=self.canSend))


    # 返信用のbuttonを送信
    try:
      await report_thread.send(view=view)
    except Exception:
      return

    # リアクションを付ける
    await message.add_reaction("✅")



async def setup(bot):
  await bot.add_cog(ReplyToReply(bot))