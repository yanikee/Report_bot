from discord.ext import commands
import discord

import os
import json
import aiofiles
import asyncio
import datetime

from modules import error
from const import EMOJI_DICT



class PticketSendFiles(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_interaction(self, interaction:discord.Interaction):
    try:
      custom_id = interaction.data["custom_id"]
    except KeyError:
      return


    # スレッド内での返信編集
    if custom_id == "pticket_send_file":
      path = f"data/pticket/pticket/{interaction.guild.id}.json"
      if not os.path.exists(path):
        e = f"[ERROR[2-2-01]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\nJson file was not found"
        print(e)
        embed=await error.generate(code="2-2-01")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

      if interaction.message.embeds[0].description == "下のボタンから編集してください。":
        custom_id = "pticket_send_files_process"

      # 返信パネルのメッセージを編集していた場合の警告メッセージ
      else:
        # embedの定義
        embed = discord.Embed(
          description="編集中の返信メッセージが全て削除されます。\nよろしいですか？",
          color=0xFF0000,
        )

        # viewの定義
        view = discord.ui.View()
        button_1 = discord.ui.Button(label="戻る", emoji=EMOJI_DICT["arrow_back"], custom_id="pticket_send_files_return", style=discord.ButtonStyle.gray)
        button_2 = discord.ui.Button(label="ファイル送信に進む", custom_id="pticket_send_files_process", style=discord.ButtonStyle.primary)
        view.add_item(button_1)
        view.add_item(button_2)

        await interaction.response.edit_message(embeds=[interaction.message.embeds[0], embed], view=view)
        return


    if custom_id == "pticket_send_files_process":
      # ファイル送信のembedを定義, 送信
      embed = discord.Embed(
        description="この埋め込みに__**返信する形**__でファイルを送信してください。(60秒以内)\n__**メンションはON**__にしてください。\n\n"
                    "⚠️注意⚠️\n送信されたファイルは、確認なしにすぐにユーザーに送信されます。ご注意ください。",
        color=0x95FFA1,
      )
      await interaction.response.edit_message(embed=embed, view=None)

      # ファイル送信を待つ
      def check(message):
        return message.channel == interaction.channel and message.reference and message.attachments
      try:
        message = await self.bot.wait_for('message', timeout=60.0, check=check)
      except asyncio.TimeoutError:
        await interaction.message.delete()
        await interaction.followup.send('タイムアウトしました。\nメッセージが受信されませんでした。', ephemeral=True)
        await self.add_reply(interaction)
        return

      # pticket者を取得
      path = f"data/pticket/pticket/{interaction.guild.id}.json"
      async with aiofiles.open(path, encoding='utf-8', mode="r") as f:
        contents = await f.read()
      pticket_dict = json.loads(contents)

      try:
        user_id = pticket_dict[str(interaction.channel.id)]
      except KeyError:
        e = f"\n[ERROR[2-2-02]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\n- CHANNEL_ID:{interaction.channel.id}\nPticket user_id was not found\n"
        print(e)
        embed=await error.generate(code="2-2-02")
        await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.message.delete()
        await self.add_reply(interaction)
        return

      try:
        user = await interaction.guild.fetch_member(user_id)
      except Exception:
        embed=await error.generate(code="2-2-03")
        await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.message.delete()
        await self.add_reply(interaction)
        return

      # embedを定義
      embed = discord.Embed(
        url = interaction.channel.jump_url,
        description="## 匿名Ticket\n"
                    f"あなたの匿名Ticketに、『{interaction.guild.name}』の管理者からファイルが届きました。\n"
                    f"- __**このメッセージに返信**__(右クリック→返信)すると、このサーバーの管理者に届きます。",
        color=0xc8e1ff,
      )
      embed.set_footer(
        text=f"匿名Ticket | {interaction.guild.name}",
        icon_url=interaction.guild.icon.replace(format='png').url if interaction.guild.icon else None,
      )

      #  attachments to files
      try:
        files = [await attachment.to_file() for attachment in message.attachments]
      except Exception as e:
        e = f"\n[ERROR[2-2-04]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\n{e}\n"
        print(e)
        embed=await error.generate(code="2-2-04")
        await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.message.delete()
        await self.add_reply(interaction)
        return

      # fileを返信する
      try:
        await user.send(embed=embed, files=files)
      except discord.errors.Forbidden:
        embed=await error.generate(code="2-2-05")
        await interaction.followup.send(embed=embed)
        await interaction.message.delete()
        return
      except Exception as e:
        e = f"\n[ERROR[2-2-06]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\n{e}\n"
        print(e)
        embed=await error.generate(code="2-2-06")
        await interaction.followup.send(embed=embed)
        await interaction.message.delete()
        await self.add_reply(interaction)
        return

      # 確認メッセージを送信
      embed = discord.Embed(
        description=f"{interaction.user.mention}がファイルを送信しました。",
        color=0x95FFA1,
      )
      await interaction.message.delete()
      await message.add_reaction("✅")
      await interaction.channel.send(embed=embed)
      await self.add_reply(interaction)


    # 「戻る」を選択した場合
    elif custom_id == "pticket_send_files_return":
      view = discord.ui.View()
      button_0 = discord.ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"pticket_edit_reply", style=discord.ButtonStyle.primary, row=0)
      button_1 = discord.ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"pticket_send", style=discord.ButtonStyle.red, row=0)
      button_2 = discord.ui.Button(emoji=EMOJI_DICT["upload_file"], label="ファイル送信", custom_id=f"pticket_send_file", style=discord.ButtonStyle.green, row=1)
      view.add_item(button_0)
      view.add_item(button_1)
      view.add_item(button_2)

      await interaction.response.edit_message(embed=interaction.message.embeds[0], view=view)


  async def add_reply(self, interaction):
    await interaction.channel.add_user(interaction.user)

    # 追加返信ボタン設置
    view = discord.ui.View()
    button_1 = discord.ui.Button(label="追加で返信", emoji=EMOJI_DICT["add"], custom_id="pticket_add_reply", style=discord.ButtonStyle.gray)
    view.add_item(button_1)
    await interaction.channel.send(view=view)



async def setup(bot):
  await bot.add_cog(PticketSendFiles(bot))
