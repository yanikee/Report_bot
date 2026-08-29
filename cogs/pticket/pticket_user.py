import re

from discord import DMChannel, Embed, Message, MessageType, components, ui
from discord.ext import commands

from bot import ReportBot
from modules import error
from modules.functions import (
  create_reply_view,
  get_files,
  get_reply_view_data,
  raise_on_guild_block,
  resolve_text_channel,
  user_cooldown,
)


class PticketUser(commands.Cog):
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

      if "匿名Ticket | " not in content:
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

      if not footer_text:
        return

      if "匿名ticket |" not in footer_text and "匿名Ticket |" not in footer_text:
        return

      pticket_msg_url = embed.url
      if not pticket_msg_url:
        return

      match = re.search(r'channels/(\d+)/(\d+)/(\d+)', pticket_msg_url)
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
      pticket_msg = await channel.fetch_message(message_id)
    except Exception as e:
      self.bot.log(f"メッセージ取得に失敗: {e}", "ERROR")
      msg = "スレッドが取得できませんでした"
      await error.send_error(msg, channel=message.channel)
      return

    pticket_thread = pticket_msg.thread

    if not pticket_thread:
      guild_data["ticket_count"] += 1
      name = f"private_pticket-{str(guild_data["ticket_count"]).zfill(4)}"

      try:
        pticket_thread = await pticket_msg.create_thread(name=name)
      except Exception as e:
        self.bot.log(f"スレッド作成に失敗: {e}", "ERROR")
        msg = "スレッドが作成できませんでした"
        await error.send_error(msg, channel=message.channel)
        return

      await self.db.upsert_guild_settings(guild_data)

      content, medias = get_reply_view_data(pticket_msg)
      files = await get_files(medias)

      view = ui.LayoutView()

      ticket_mention_role_id = guild_data["ticket_mention_role_id"]
      if ticket_mention_role_id:
        view.add_item(ui.TextDisplay(f"<@&{ticket_mention_role_id}>"))

      container = ui.Container(accent_color=0xc8e1ff)
      container.add_item(ui.TextDisplay("## 匿名Ticket"))
      container.add_item(ui.Separator())
      container.add_item(ui.TextDisplay("## Ticket内容"))
      container.add_item(ui.TextDisplay(content, id=999))

      for file in files:
        container.add_item(ui.File(media=file))

      view.add_item(container)

      await pticket_msg.edit(view=view, attachments=files)

    # アーカイブされていた場合、親チャンネルに通知
    if pticket_thread.archived:
      embed = Embed(
        title="お知らせ",
        description=f"{pticket_thread.mention}に、新しい返信が届きました",
        color=0xff33ff,
      )
      embed.set_footer(text="スレッドがアーカイブされていたため通知されました")
      await channel.send(embed=embed)

    panel_msg = None
    async for msg in pticket_thread.history(limit=5):
      if msg.components:
        panel_msg = msg
        await msg.delete()
        break


    view = ui.LayoutView()

    container = ui.Container(accent_color=0xc8e1ff)
    container.add_item(ui.TextDisplay("## 匿名Ticket"))
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
      await pticket_thread.send(view=view, files=files)
    except Exception as e:
      self.bot.log(f"スレッドへの送信に失敗: {e}", "ERROR")
      msg = "スレッドにメッセージを送信できませんでした"
      await error.send_error(msg, channel=message.channel)
      return


    if panel_msg:
      view = ui.LayoutView().from_message(panel_msg)

    else:
      view, _ = await create_reply_view("pticket")

    try:
      await pticket_thread.send(view=view)
    except Exception as e:
      self.bot.log(f"スレッドへの送信に失敗: {e}", "ERROR")
      await message.add_reaction("✖")
      return

    await message.add_reaction("✅")



async def setup(bot):
  await bot.add_cog(PticketUser(bot))
