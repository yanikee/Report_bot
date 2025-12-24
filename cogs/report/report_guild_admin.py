from discord.ext import commands
from discord import ui
import discord

from modules import error
from modules.db import DB
from modules.functions import create_reply_view, get_reply_view_data, get_files
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

    guild, channel, message = (interaction.guild, interaction.channel, interaction.message)
    if not guild or not channel or not message:
      return

    custom_id = data.get("custom_id")

    if custom_id == "report_create_thread":
      guild_data = await self.db.get_guild_settings(guild.id)
      if not guild_data:
        msg = "サーバーデータが見つかりませんでした\n`/settings`を実行してください"
        await error.send_error(msg, interaction)
        return

      guild_data["report_count"] += 1
      name = f"private_report-{str(guild_data["report_count"]).zfill(4)}"

      try:
        thread = await message.create_thread(name=name)
      except Exception:
        msg = "スレッドを作成できませんでした\n権限を確認してください"
        await error.send_error(msg, interaction)
        return

      await message.edit(view=None)

      view, files = await create_reply_view()

      await thread.send(view=view)
      await interaction.delete_original_response()
      return

    elif custom_id == "report_edit_reply":
      modal = EditReplyModal(self.bot, message)
      await interaction.response.send_modal(modal)
      return


    elif custom_id == "report_file_delete":
      values = data.get("values")
      if not values:
        return

      await interaction.response.defer(thinking=True, ephemeral=True)

      file_name = values[0]
      content, medias = get_reply_view_data(message)
      existing_files = [f for f in (await get_files(medias)) if file_name not in f.filename]
      view, files = await create_reply_view(content, list(existing_files))
      await interaction.followup.edit_message(message.id, view=view, attachments=files)
      await interaction.delete_original_response()
      return


    elif custom_id == "report_send":
      await interaction.response.defer(thinking=True)

      if not isinstance(channel, discord.Thread):
        return

      guild_data = await self.db.get_guild_settings(guild.id)
      if not guild_data:
        msg = "サーバーデータが取得できませんでした"
        await error.send_error(msg, interaction, followup=True)
        return

      thread_data = await self.db.get_thread(channel.id)
      if not thread_data:
        msg = "スレッドデータが取得できませんでした"
        await error.send_error(msg, interaction, followup=True)
        return

      user_id = thread_data["user_id"]

      user = self.bot.get_user(user_id)
      if not user:
        try:
          user = await self.bot.fetch_user(user_id)
        except Exception:
          msg = "ユーザーデータが取得できませんでした"
          await error.send_error(msg, interaction, followup=True)
          return

      content, medias = get_reply_view_data(message)
      files = await get_files(medias)

      view = ui.LayoutView()

      container = ui.Container(accent_color=0xffe7ab)
      icon_url = guild.icon.url if guild.icon else "https://example.com"

      thumbnail = ui.Thumbnail(icon_url, description=f"{guild.id}/{channel.parent_id}/{channel.id}")
      section = ui.Section(accessory=thumbnail)
      section.add_item(ui.TextDisplay("# 匿名Report"))
      section.add_item(ui.TextDisplay(f"- **{guild.name}**の管理者からメッセージが届きました"))
      section.add_item(ui.TextDisplay("- __**このメッセージに返信**__すると管理者に届きます"))
      container.add_item(section)

      container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

      container.add_item(ui.TextDisplay("## 返信内容"))
      container.add_item(ui.TextDisplay(content))

      if files:
        container.add_item(ui.TextDisplay("## 添付ファイル"))
        for file in files:
          container.add_item(ui.File(file))

      container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

      container.add_item(ui.TextDisplay(f"匿名Report｜{guild.name}", id=998))

      view.add_item(container)

      try:
        await user.send(view=view, files=files)
      except Exception:
        msg = "送信できませんでした"
        await error.send_error(msg, channel=channel)
        return

      view = ui.LayoutView()

      container = ui.Container(accent_color=0x95FFA1)
      container.add_item(ui.TextDisplay(f"返信：{interaction.user.display_name}"))
      container.add_item(ui.TextDisplay("## 返信内容"))
      container.add_item(ui.TextDisplay(content))

      if files:
        container.add_item(ui.TextDisplay(f"## 添付ファイル"))
        for file in files:
          container.add_item(ui.File(file))

      view.add_item(container)

      await message.edit(view=view)
      await message.add_reaction("✅")

      await interaction.delete_original_response()

      await channel.add_user(interaction.user)

      view = discord.ui.View()
      button = discord.ui.Button(label="追加で返信", emoji=EMOJI_DICT["add"], custom_id="report_add_reply", style=discord.ButtonStyle.gray)
      view.add_item(button)
      await channel.send(view=view)
      return


    elif custom_id == "report_add_reply" or custom_id == "add_reply":
      view, _ = await create_reply_view()

      await interaction.response.edit_message(view=view)
      return


    elif custom_id == "report_cancel":
      if not isinstance(channel, discord.Thread):
        return

      await message.delete()

      view = discord.ui.View()
      button = discord.ui.Button(label="追加で返信", emoji=EMOJI_DICT["add"], custom_id="report_add_reply", style=discord.ButtonStyle.gray)
      view.add_item(button)
      await channel.send(view=view)
      return


class EditReplyModal(ui.Modal):
  def __init__(self, bot: commands.Bot, msg: discord.Message):
    super().__init__(title=f'報告への返信')
    self.bot = bot
    self.msg = msg

    default: str | None = None
    self.files: list[discord.UnfurledMediaItem] = []

    content, self.files = get_reply_view_data(msg)

    if "下のボタンから編集してください。" in content:
      default = None
      self.disabled = True
    else:
      default = content
      self.disabled = False

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
      await error.send_error(msg, interaction)
      return

    existing_files: list[discord.File] = []
    if self.files:
      await interaction.response.defer(thinking=True, ephemeral=True)

      existing_files = await get_files(self.files)

    else:
      await interaction.response.defer()

    values = existing_files + self.file_input.values

    view, files = await create_reply_view(self.reply_input.value, values)

    filenames = [file.filename for file in files]
    if len(filenames) != len(set(filenames)):
      msg = "同一ファイルが含まれています"
      await error.send_error(msg, interaction=interaction, followup=True)
      return

    await interaction.followup.edit_message(self.msg.id, view=view, attachments=files)

    if self.files:
      await interaction.delete_original_response()


async def setup(bot):
  await bot.add_cog(ReportGuildAdmin(bot))
