from discord.ext import commands
import discord

import os
import json
import aiofiles
import datetime

from modules import error
from const import EMOJI_DICT



class PticketReply(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_interaction(self, interaction:discord.Interaction):
    try:
      custom_id = interaction.data["custom_id"]
    except KeyError:
      return

    # Pticketのやつがなかった場合 -> return
    if custom_id in ["pticket_edit_reply", "pticket_send", "pticket_add_reply"]:
      path = f"data/pticket/pticket/{interaction.guild.id}.json"
      if not os.path.exists(path):
        e = f"[ERROR[2-1-01]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\nJson file was not found"
        print(e)
        embed=await error.generate(code="2-1-01")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return


    # スレッド内での返信編集
    if custom_id == "pticket_edit_reply":
      modal = EditReplyModal(self.bot, interaction.message)
      await interaction.response.send_modal(modal)


    elif custom_id == "pticket_send":
      async with aiofiles.open(path, encoding='utf-8', mode="r") as f:
        contents = await f.read()
      pticket_dict = json.loads(contents)

      # pticket者を取得
      try:
        user_id = pticket_dict[str(interaction.channel.id)]
      except KeyError:
        e = f"\n[ERROR[2-1-02]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\n- CHANNEL_ID:{interaction.channel.id}\nPticket user was not found\n"
        print(e)
        embed=await error.generate(code="2-1-02")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

      try:
        user = await interaction.guild.fetch_member(user_id)
      except Exception:
        embed=await error.generate(code="2-1-03")
        await interaction.response.send_message(embed=embed)
        return

      # embedを定義
      # embed_1: お知らせ
      # embed_2: 返信内容
      embed = discord.Embed(
        url = interaction.channel.jump_url,
        description="## 匿名Ticket\n"
                    f"あなたの匿名Ticketに、 『{interaction.guild.name}』 の管理者から返信が届きました。\n"
                    f"- __**このメッセージに返信**__(右クリック→返信)すると、このサーバーの管理者に届きます。\n\n"
                    f"## 返信内容\n{interaction.message.embeds[0].description}",
        color=0xc8e1ff,
      )
      embed.set_footer(
        text=f"匿名Ticket | {interaction.guild.name}",
        icon_url=interaction.guild.icon.replace(format='png').url if interaction.guild.icon else None,
      )

      # 返信する
      try:
        await user.send(embed=embed)
      except discord.errors.Forbidden:
        embed=await error.generate(code="2-1-04")
        await interaction.response.send_message(embed=embed)
        return
      except Exception as e:
        e = f"\n[ERROR[2-1-05]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\n{e}\n"
        print(e)
        embed=await error.generate(code="2-1-05")
        await interaction.response.send_message(embed=embed)
        return

      # 返信パネルを編集する
      embed = interaction.message.embeds[0]
      embed.set_author(
        name=f"返信：{interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None,
      )
      await interaction.response.edit_message(embed=embed, view=None)
      await interaction.message.add_reaction("✅")

      # 返信したユーザーをスレッドに参加させる
      await interaction.channel.add_user(interaction.user)

      # 追加返信ボタン設置
      view = discord.ui.View()
      button = discord.ui.Button(label="追加で返信", emoji=EMOJI_DICT["add"], custom_id="pticket_add_reply", style=discord.ButtonStyle.gray,)
      view.add_item(button)
      await interaction.channel.send(view=view)


    # 追加返信ボタンが押されたときの処理
    elif custom_id == "pticket_add_reply":
      view = discord.ui.View()
      button_0 = discord.ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"pticket_edit_reply", style=discord.ButtonStyle.primary, row=0)
      button_1 = discord.ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"pticket_send", style=discord.ButtonStyle.red, row=0, disabled=True)
      button_2 = discord.ui.Button(emoji=EMOJI_DICT["upload_file"], label="ファイル送信", custom_id=f"pticket_send_file", style=discord.ButtonStyle.green, row=1)
      button_3 = discord.ui.Button(emoji=EMOJI_DICT["delete"], label="もう返信しない", custom_id=f"pticket_cancel", style=discord.ButtonStyle.gray, row=2)
      view.add_item(button_0)
      view.add_item(button_1)
      view.add_item(button_2)
      view.add_item(button_3)

      embed=discord.Embed(
        title="返信内容",
        description="下のボタンから編集してください。",
        color=0x95FFA1,
      )
      await interaction.response.edit_message(embed=embed, view=view)


    # もう返信しないボタンが押されたときの処理
    elif custom_id == "pticket_cancel":
      await interaction.message.delete()

      # 追加返信ボタン設置
      view = discord.ui.View()
      button = discord.ui.Button(label="追加で返信", emoji=EMOJI_DICT["add"], custom_id="pticket_add_reply", style=discord.ButtonStyle.gray,)
      view.add_item(button)
      await interaction.channel.send(view=view)


class EditReplyModal(discord.ui.Modal):
  def __init__(self, bot, msg):
    super().__init__(title=f'匿名Ticketへの返信用modal')
    self.bot = bot
    self.msg = msg

    # modalのdefaultを定義
    if "下のボタンから編集してください。" in self.msg.embeds[0].description:
      default = None
    else:
      default = self.msg.embeds[0].description

    self.reply = discord.ui.TextInput(
      label="返信内容を入力（送信ボタンで一時保存できます。）",
      style=discord.TextStyle.long,
      default=default,
      required=True,
      row=0
    )
    self.add_item(self.reply)

  async def on_submit(self, interaction: discord.Interaction):
    # NOTE: 編集が適用されたことが分かりやすいように、わざとdeferしてる
    await interaction.response.defer()
    self.msg.embeds[0].description = self.reply.value
    self.msg.embeds[0].set_author(
      name=f"一時保存：{interaction.user.display_name}",
      icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None,
    )

    if self.reply.value == "下のボタンから編集してください。":
      button_bool = True
    else:
      button_bool = False

    view = discord.ui.View()
    button_0 = discord.ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"pticket_edit_reply", style=discord.ButtonStyle.primary, row=0)
    button_1 = discord.ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"pticket_send", style=discord.ButtonStyle.red, row=0, disabled=button_bool)
    button_2 = discord.ui.Button(emoji=EMOJI_DICT["upload_file"], label="ファイル送信", custom_id=f"pticket_send_file", style=discord.ButtonStyle.green, row=1)
    view.add_item(button_0)
    view.add_item(button_1)
    view.add_item(button_2)

    await interaction.followup.edit_message(self.msg.id, embed=self.msg.embeds[0], view=view)



async def setup(bot):
  await bot.add_cog(PticketReply(bot))
