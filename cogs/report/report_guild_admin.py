from discord.ext import commands
import discord

import os
import json
import aiofiles
import datetime

from modules import error
from const import EMOJI_DICT



class ReportGuildAdmin(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_interaction(self, interaction:discord.Interaction):
    try:
      custom_id = interaction.data["custom_id"]
    except KeyError:
      return

    # privateのやつがなかった場合 -> return
    if custom_id in ["report_create_thread", "report_edit_reply", "report_send"]:
      path = f"data/report/private_report/{interaction.guild.id}.json"
      if not os.path.exists(path):
        e = f"[ERROR[3-1-01]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\nJson file was not found"
        print(e)
        embed=await error.generate(code="3-1-01")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return


    if custom_id == "report_create_thread":
      # buttonの削除
      await interaction.message.edit(view=None)

      # reply_numを定義
      path = f"data/report/guilds/{interaction.guild.id}.json"
      async with aiofiles.open(path, encoding='utf-8', mode="r") as f:
        contents = await f.read()
      report_dict = json.loads(contents)
      # 存在しなかった場合は作る
      if not report_dict.get("reply_num"):
        report_dict["reply_num"] = 0
      report_dict["reply_num"] += 1
      # 保存
      async with aiofiles.open(path, mode="w") as f:
        contents = json.dumps(report_dict, indent=2, ensure_ascii=False)
        await f.write(contents)

      # thread作成, 送信
      thread = await interaction.message.create_thread(name=f"private_report-{str(report_dict['reply_num']).zfill(4)}")

      embed=discord.Embed(
        title="返信内容",
        description="下のボタンから編集してください。",
        color=0x95FFA1,
      )
      view = discord.ui.View()
      button_0 = discord.ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"report_edit_reply", style=discord.ButtonStyle.primary, row=0)
      button_1 = discord.ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"report_send", style=discord.ButtonStyle.red, row=0, disabled=True)
      button_2 = discord.ui.Button(emoji=EMOJI_DICT["upload_file"], label="ファイル送信", custom_id=f"report_send_file", style=discord.ButtonStyle.green, row=1)
      view.add_item(button_0)
      view.add_item(button_1)
      view.add_item(button_2)

      await thread.send(embed=embed, view=view)

      await interaction.response.send_message("こちらのスレッドから返信を行えます。", ephemeral=True)


    # スレッド内での返信編集
    elif custom_id == "report_edit_reply":
      modal = EditReplyModal(self.bot, interaction.message)
      await interaction.response.send_modal(modal)


    elif custom_id == "report_send":
      # 報告者を取得
      async with aiofiles.open(path, encoding='utf-8', mode="r") as f:
        contents = await f.read()
      private_dict = json.loads(contents)
      reporter_id = private_dict.get(str(interaction.channel.id))

      # reporter_idがNoneの場合->return
      if not reporter_id:
        e = f"\n[ERROR[3-1-02]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\n- CHANNEL_ID:{interaction.channel.id}\nReporter_id was not found\n"
        print(e)
        embed=await error.generate(code="3-1-02")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

      try:
        reporter = await interaction.guild.fetch_member(reporter_id)
      except Exception:
        embed=await error.generate(code="3-1-03")
        await interaction.response.send_message(embed=embed)
        return

      # embedを定義
      embed = discord.Embed(
        url=interaction.channel.jump_url,
        description="## 匿名Report\n"
                    f"あなたの報告に、『{interaction.guild.name}』の管理者から返信が届きました。\n"
                    f"- __**このメッセージに返信**__(右クリック→返信)すると、このサーバーの管理者に届きます。\n\n"
                    f"## 返信内容\n{interaction.message.embeds[0].description}",
        color=0xffe7ab,
      )
      embed.set_footer(
        text=f"匿名Report | {interaction.guild.name}",
        icon_url=interaction.guild.icon.replace(format='png').url if interaction.guild.icon else None,
      )

      # 返信を送信する
      try:
        await reporter.send(embed=embed)
      except discord.errors.Forbidden:
        embed=await error.generate(code="3-1-04")
        await interaction.response.send_message(embed=embed)
        return
      except Exception as e:
        e = f"\n[ERROR[3-1-05]]{datetime.datetime.now()}\n- GUILD_ID:{interaction.guild.id}\n{e}\n"
        print(e)
        embed=await error.generate(code="3-1-05")
        await interaction.response.send_message(embed=embed, ephemeral=True)
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
      button = discord.ui.Button(label="追加で返信", emoji=EMOJI_DICT["add"], custom_id="report_add_reply", style=discord.ButtonStyle.gray)
      view.add_item(button)
      await interaction.channel.send(view=view)


    # 追加返信ボタンが押されたときの処理
    elif custom_id == "report_add_reply" or custom_id == "add_reply":
      embed=discord.Embed(
        title="返信内容",
        description="下のボタンから編集してください。",
        color=0x95FFA1,
      )
      view = discord.ui.View()
      button_0 = discord.ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"report_edit_reply", style=discord.ButtonStyle.primary, row=0)
      button_1 = discord.ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"report_send", style=discord.ButtonStyle.red, row=0, disabled=True)
      button_2 = discord.ui.Button(emoji=EMOJI_DICT["upload_file"], label="ファイル送信", custom_id=f"report_send_file", style=discord.ButtonStyle.green, row=1)
      button_3 = discord.ui.Button(emoji=EMOJI_DICT["delete"], label="もう返信しない", custom_id=f"report_cancel", style=discord.ButtonStyle.gray, row=2)
      view.add_item(button_0)
      view.add_item(button_1)
      view.add_item(button_2)
      view.add_item(button_3)

      await interaction.response.edit_message(embed=embed, view=view)


    # もう返信しないボタンが押されたときの処理
    elif custom_id == "report_cancel":
      await interaction.message.delete()

      # 追加返信ボタン設置
      view = discord.ui.View()
      button = discord.ui.Button(label="追加で返信", emoji=EMOJI_DICT["add"], custom_id="report_add_reply", style=discord.ButtonStyle.gray)
      view.add_item(button)
      await interaction.channel.send(view=view)


class EditReplyModal(discord.ui.Modal):
  def __init__(self, bot, msg):
    super().__init__(title=f'報告への返信用modal')
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
    button_0 = discord.ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"report_edit_reply", style=discord.ButtonStyle.primary, row=0)
    button_1 = discord.ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"report_send", style=discord.ButtonStyle.red, row=0, disabled=button_bool)
    button_2 = discord.ui.Button(emoji=EMOJI_DICT["upload_file"], label="ファイル送信", custom_id=f"report_send_file", style=discord.ButtonStyle.green, row=1)
    view.add_item(button_0)
    view.add_item(button_1)
    view.add_item(button_2)

    await interaction.followup.edit_message(self.msg.id, embed=self.msg.embeds[0], view=view)



async def setup(bot):
  await bot.add_cog(ReportGuildAdmin(bot))
