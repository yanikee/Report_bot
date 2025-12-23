from discord.ext import commands
from discord import ui, components
import discord

import io
import json
import aiohttp
import aiofiles
import datetime

from modules import error
from modules.db import DB
from modules.functions import get_reply_view
from const import EMOJI_DICT



class ReportGuildAdmin(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.db = DB()

  @commands.Cog.listener()
  async def on_interaction(self, interaction: discord.Interaction):
    data = interaction.data
    if not data:
      return

    guild = interaction.guild
    if not guild:
      return

    custom_id = data.get("custom_id")

    message = interaction.message
    if not message:
      return

    if custom_id == "report_create_thread":
      guild_data = await self.db.get_guild_settings(guild.id)
      if not guild_data:
        return

      guild_data["report_count"] += 1
      name = f"private_report-{str(guild_data["report_count"]).zfill(4)}"

      try:
        thread = await message.create_thread(name=name)
      except Exception:
        return

      # buttonの削除
      await message.edit(view=None)

      view, files = await get_reply_view()

      await thread.send(view=view)

      await interaction.response.send_message("このスレッドから返信を行えます。", ephemeral=True)


    # スレッド内での返信編集
    elif custom_id == "report_edit_reply":
      modal = EditReplyModal(self.bot, message)
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


class EditReplyModal(ui.Modal):
  def __init__(self, bot: commands.Bot, msg: discord.Message):
    super().__init__(title=f'報告への返信')
    self.bot = bot
    self.msg = msg

    default: str | None = None
    self.files: list[discord.UnfurledMediaItem] = []

    if isinstance(msg.components[0], components.Container):
      children = msg.components[0].children

      for child in children:
        if isinstance(child, components.TextDisplay) and child.id == 999:
          if "下のボタンから編集してください。" in child.content:
            default = None
            self.disabled = True
          else:
            default = child.content
            self.disabled = False

        if isinstance(child, components.FileComponent):
          self.files.append(child.media)


    self.reply_input = discord.ui.TextInput(
      style=discord.TextStyle.long,
      default=default,
      required=False,
    )
    self.file_input = ui.FileUpload(
      required=False,
      max_values=3
    )
    self.add_item(ui.Label(text="返信内容", component=self.reply_input))
    self.add_item(ui.Label(text="添付ファイル", component=self.file_input))


  async def on_submit(self, interaction: discord.Interaction):

    if len(self.files + self.file_input.values) > 3:
      msg = "一度に添付できるファイルは3件までです"
      await error.send_error(interaction, msg)
      return

    existing_files: list[discord.File] = []
    if self.files:
      await interaction.response.defer(thinking=True, ephemeral=True)

      async with aiohttp.ClientSession() as session:
        for item in self.files:
          async with session.get(item.url) as resp:
            data = await resp.read()
            filename = item.url.split('/')[-1].split('?')[0]
            existing_files.append(discord.File(io.BytesIO(data), filename=filename))

    else:
      await interaction.response.defer()

    values = existing_files + self.file_input.values

    view, files = await get_reply_view(self.reply_input.value, values)

    filenames = [file.filename for file in files]
    if len(filenames) != len(set(filenames)):
      msg = "同一ファイルが含まれています"
      await error.send_error(interaction, msg, True)
      return

    await interaction.followup.edit_message(self.msg.id, view=view, attachments=files)

    if self.files:
      await interaction.delete_original_response()


async def setup(bot):
  await bot.add_cog(ReportGuildAdmin(bot))
