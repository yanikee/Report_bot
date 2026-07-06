from discord.ext import commands
from discord import components, Message, Embed, DMChannel, MessageType

from bot import ReportBot



class CheckReply(commands.Cog):
  def __init__(self, bot: ReportBot):
    self.bot = bot

  async def is_not_reply(self, message: Message):
    embed = Embed(
      description="# 返信できていません！\nbotからの匿名Report/匿名Ticketのメッセージに対して、「右クリック」→「返信」を行ってください！",
      color=0xff4b00,
    )
    embed.set_footer(text="このメッセージは15秒後に削除されます")

    await message.reply(embed=embed, delete_after=15)
    await message.add_reaction("❌")
    return

  @commands.Cog.listener()
  async def on_message(self, message: Message):
    if not isinstance(message.channel, DMChannel):
      return

    if message.author.bot:
      return

    reference = message.reference

    if message.type != MessageType.reply or not reference:
      await self.is_not_reply(message)
      return

    msg = reference.cached_message
    if not msg:
      msg_id = reference.message_id
      if not msg_id:
        await self.is_not_reply(message)
        return

      try:
        msg = await message.channel.fetch_message(msg_id)
      except Exception:
        await self.is_not_reply(message)
        return


    if not msg.embeds:
      target_id = 998
      content = next((
        child.content
        for comp in msg.components if isinstance(comp, components.Container)
        for child in comp.children
        if isinstance(child, components.TextDisplay) and child.id == target_id
      ), "")

      if not "匿名Ticket | " in content and not "匿名Report | " in content:
        await self.is_not_reply(message)
        return

    else:
      embed = msg.embeds[0]
      footer_text = embed.footer.text

      if not footer_text:
        await self.is_not_reply(message)
        return

      if (
        "匿名ticket |" not in footer_text and
        "匿名Ticket |" not in footer_text and
        "匿名Report | " not in footer_text and
        "匿名報告 | " not in footer_text
      ):
        await self.is_not_reply(message)
        return


async def setup(bot):
  await bot.add_cog(CheckReply(bot))