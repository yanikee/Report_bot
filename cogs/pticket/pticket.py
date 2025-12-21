from discord.ext import commands
import discord

import os
import json
import aiofiles
import datetime

from modules import error, functions
from const import EMOJI_DICT



class PrivateTicket(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.user_cooldowns = {}

  # private_ticketからthreadを作る
  @commands.Cog.listener()
  async def on_interaction(self, interaction):
    try:
      if interaction.data["custom_id"] != "private_ticket":
        return
    except KeyError:
      return

    path = f"data/pticket/guilds/{interaction.guild.id}.json"
    if not os.path.exists(path):
      embed=await error.generate(code="2-4-01")
      await interaction.response.send_message(embed=embed, ephemeral=True)
      return

    # guild_block
    embed = await functions.is_guild_block(bot=self.bot,guild=interaction.guild, user_id=interaction.user.id)
    if embed:
      await interaction.response.send_message(embed=embed, ephemeral=True)
      return

    # cooldown
    embed, self.user_cooldowns = functions.user_cooldown(interaction.user.id, self.user_cooldowns)
    if embed:
      await interaction.response.send_message(embed=embed, ephemeral=True)
      return

    # DMにテストメッセージを送信
    try:
      await interaction.user.send("テストメッセージ", silent=True, delete_after=0.1)
    except Exception:
      embed=await error.generate(code="2-4-02")
      await interaction.response.send_message(embed=embed, ephemeral=True)
      return

    modal = PrivateTicketModal(self.bot)
    await interaction.response.send_modal(modal)

    # 匿名Ticket buttonの絵文字を旧から新に
    if interaction.message.components:
      for button in interaction.message.components[0].children:
        if isinstance(button, discord.Button):
          if button.emoji.name == "🔖": 
            view=discord.ui.View()
            button_0 = discord.ui.Button(label="匿名Ticket", emoji=EMOJI_DICT["new_label"], custom_id=f"private_ticket", style=discord.ButtonStyle.primary, disabled=False, row=0)
            view.add_item(button_0)
            await interaction.message.edit(view=view)


class PrivateTicketModal(discord.ui.Modal):
  def __init__(self, bot):
    super().__init__(title=f'匿名Ticketモーダル')
    self.bot = bot

    self.first_pticket = discord.ui.TextInput(
      label="Ticket内容を入力",
      style=discord.TextStyle.long,
      default=None,
      placeholder="（ちなみに）\n後ほどbotのDMに、添付ファイルなどを送信できます。",
      required=True,
      row=0
    )
    self.add_item(self.first_pticket)

  async def on_submit(self, interaction: discord.Interaction):
    await interaction.response.defer()
    # embedの定義
    embed=discord.Embed(
      title="匿名Ticket",
      description=self.first_pticket.value,
      color=0xc8e1ff,
    )

    # pticket_channel, mention_roleの取得
    path = f"data/pticket/guilds/{interaction.guild.id}.json"
    async with aiofiles.open(path, encoding='utf-8', mode="r") as f:
      contents = await f.read()
    ticket_dict = json.loads(contents)
    cha = interaction.guild.get_channel(ticket_dict.get("report_send_channel"))

    # 匿名TicketチャンネルがNoneだった場合->return
    if not cha:
      embed=await error.generate(code="2-4-03")
      await interaction.followup.send(f"### あなたの匿名Ticket内容\n　{self.first_pticket.value}", embed=embed, ephemeral=True)
      return

    if "mention_role" in ticket_dict:
      mention_role_id = ticket_dict["mention_role"]
    else:
      mention_role_id = None

    # Ticketを送信
    if mention_role_id:
      msg = f"<@&{mention_role_id}>\n{self.bot.user.mention}"
    else:
      msg = self.bot.user.mention

    try:
      msg = await cha.send(msg, embed=embed)
    except Exception as e:
      e = f"\n[ERROR[2-4-04]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\n- CHANNEL_ID:{cha.id}\n{e}\n"
      print(e)
      embed=await error.generate(code="2-4-04")
      await interaction.followup.send(f"### あなたの匿名Ticket内容\n　{self.first_pticket.value}", embed=embed, ephemeral=True)
      return

    # pticket送信者idを保存{msg.id: user.id}
    path = f"data/pticket/pticket/{interaction.guild.id}.json"
    if os.path.exists(path):
      async with aiofiles.open(path, encoding='utf-8', mode="r") as f:
        contents = await f.read()
      pticket_dict = json.loads(contents)
    else:
      pticket_dict = {}

    pticket_dict[str(msg.id)] = interaction.user.id

    async with aiofiles.open(path, mode="w") as f:
      contents = json.dumps(pticket_dict, indent=2, ensure_ascii=False)
      await f.write(contents)


    # pticket_numを定義
    path = f"data/pticket/guilds/{interaction.guild.id}.json"
    async with aiofiles.open(path, encoding='utf-8', mode="r") as f:
      contents = await f.read()
    ticket_dict = json.loads(contents)
    # 存在しない場合は作る
    if not ticket_dict.get("pticket_num"):
      ticket_dict["pticket_num"] = 0
    ticket_dict["pticket_num"] += 1
    # 保存
    async with aiofiles.open(path, mode="w") as f:
      contents = json.dumps(ticket_dict, indent=2, ensure_ascii=False)
      await f.write(contents)


    # thread作成, button送信
    thread = await msg.create_thread(name=f"private_ticket-{str(ticket_dict['pticket_num']).zfill(4)}")

    embed=discord.Embed(
      title="返信内容",
      description="下のボタンから編集してください。",
      color=0x95FFA1,
    )
    view = discord.ui.View()
    button_0 = discord.ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"pticket_edit_reply", style=discord.ButtonStyle.primary, row=0)
    button_1 = discord.ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"pticket_send", style=discord.ButtonStyle.red, row=0, disabled=True)
    button_2 = discord.ui.Button(emoji=EMOJI_DICT["upload_file"], label="ファイル送信", custom_id=f"pticket_send_file", style=discord.ButtonStyle.green, row=1)
    view.add_item(button_0)
    view.add_item(button_1)
    view.add_item(button_2)

    await thread.send(embed=embed, view=view)

    # Pticket完了確認membedを定義
    embed_1=discord.Embed(
      url=thread.jump_url,
      description=f"## 匿名Ticket\n{self.first_pticket.value}",
      color=0xc8e1ff,
    )
    embed_1.set_footer(
        text=f"匿名Ticket | {interaction.guild.name}",
        icon_url=interaction.guild.icon.replace(format='png').url if interaction.guild.icon else None,
      )

    embed_2=discord.Embed(
      description="- ファイルを添付する場合や追加で何か送信する場合は、**このメッセージに返信**する形で送信してください。\n"
                  "- あなたの情報(ユーザー名, idなど)が外部に漏れることは一切ありません。",
      color=0xc8e1ff,
    )

    # Pticket完了確認embedを送信
    try:
      await interaction.user.send(embeds=[embed_1, embed_2])
    except Exception as e:
      e = f"\n[ERROR[2-4-05]]{datetime.datetime.now()}\n- USER_ID:{interaction.user.id}\n- GUILD_ID:{interaction.guild.id}\n- CHANNEL_ID:{interaction.channel.id}\n{e}\n"
      print(e)
      embed=await error.generate(code="2-4-05")
      await interaction.followup.send(embed=embed, ephemeral=True)
      return

    # 完了msgを送信
    await interaction.followup.send("サーバー管理者に匿名Ticketが送信されました。\nDMにてサーバー管理者からの返信をお待ちください。", ephemeral=True)



async def setup(bot):
  await bot.add_cog(PrivateTicket(bot))
