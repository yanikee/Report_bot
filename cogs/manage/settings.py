from discord.ext import commands
from discord import app_commands, ui
import discord

from typing import Literal

from modules import error
from const import EMOJI_DICT
from modules.db import DB, GuildSettings


class Settings(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.db = DB()
    self.data: dict[int, GuildSettings] = {}

  @app_commands.command(name="settings", description='設定を行います')
  @discord.app_commands.guild_only()
  async def settings(self, interaction:discord.Interaction):
    guild = interaction.guild
    if not guild:
      return

    guild_data = await self.db.get_guild_settings(guild.id)
    if not guild_data:
      guild_data = await self.db.create_guild_settings(guild.id)

    self.data[guild.id] = guild_data

    view = self.settings_page_1()
    await interaction.response.send_message(view=view, ephemeral=True)


  def settings_page_1(self):
    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("**settings (1/3)**\n"
                                      "1. Report機能\n"
                                      "1. 匿名Ticket機能\n"
                                      "これらの設定を行います"))
    row = ui.ActionRow()
    row.add_item(ui.Button(label="次へ", custom_id=f"settings_page_2", style=discord.ButtonStyle.primary, row=0))
    container.add_item(row)

    view = ui.LayoutView()
    view.add_item(container)
    return view


  async def settings_page_2(self, interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
      return

    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("**settings (2/3)**\n## Report機能の設定"))

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    row1 = ui.ActionRow()
    row1.add_item(ui.ChannelSelect(
      placeholder="Report送信チャンネル",
      channel_types=[discord.ChannelType.text],
      custom_id=f"settings_select_report_channel",
      min_values=0,
      default_values=[self.data[guild.id]["report_channel_id"]]
    ))
    container.add_item(row1)

    row2 = ui.ActionRow()
    row2.add_item(ui.RoleSelect(
      placeholder="Report送信時メンションロール",
      custom_id=f"settings_report_mention_role",
      min_values=0,
      default_values=[self.data[guild.id]["report_mention_role_id"]]
    ))
    container.add_item(row2)

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    row3 = ui.ActionRow()
    row3.add_item(ui.Button(label="戻る", emoji=EMOJI_DICT["arrow_back"], custom_id=f"settings_page_1", style=discord.ButtonStyle.gray))
    row3.add_item(ui.Button(label="次へ", emoji=EMOJI_DICT["arrow_forward"], custom_id=f"settings_page_3", style=discord.ButtonStyle.gray))
    container.add_item(row3)

    view = ui.LayoutView()
    view.add_item(container)

    await interaction.response.edit_message(view=view)


  async def settings_page_3(self, interaction:discord.Interaction):
    guild = interaction.guild
    if not guild:
      return

    container = ui.Container(accent_color=0xffe7ab)
    container.add_item(ui.TextDisplay("**settings (3/3)**\n## Ticket機能の設定"))

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    row1 = ui.ActionRow()
    row1.add_item(ui.ChannelSelect(
      placeholder="Ticket送信チャンネル",
      channel_types=[discord.ChannelType.text],
      custom_id=f"settings_select_ticket_channel",
      min_values=0,
      default_values=[self.data[guild.id]["ticket_channel_id"]]
    ))
    container.add_item(row1)

    row2 = ui.ActionRow()
    row2.add_item(ui.RoleSelect(
      placeholder="Ticket送信時メンションロール",
      custom_id=f"settings_ticket_mention_role",
      min_values=0,
      default_values=[self.data[guild.id]["ticket_mention_role_id"]]
    ))
    container.add_item(row2)

    row3 = ui.ActionRow()
    row3.add_item(ui.RoleSelect(
      placeholder="Ticket開始ボタンを設置するチャンネル",
      custom_id=f"settings_report_mention_role",
      min_values=0,
      default_values=[self.data[guild.id]["ticket_mention_role_id"]]
    ))
    container.add_item(row3)

    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

    row3 = ui.ActionRow()
    row3.add_item(ui.Button(label="戻る", emoji=EMOJI_DICT["arrow_back"], custom_id=f"settings_page_2", style=discord.ButtonStyle.gray))
    row3.add_item(ui.Button(label="保存して終了", emoji=EMOJI_DICT["arrow_forward"], custom_id=f"settings_page_3", style=discord.ButtonStyle.gray))
    container.add_item(row3)

    view = ui.LayoutView()
    view.add_item(container)

    await interaction.response.edit_message(view=view)


  @commands.Cog.listener()
  async def on_interaction(self, interaction: discord.Interaction):
    if not interaction.data:
      return

    custom_id = interaction.data.get("custom_id")
    if not custom_id:
      return

    # settings_1
    if custom_id == "settings_page_1":
      view = self.settings_page_1()
      await interaction.response.edit_message(view=view)

    # settings_2
    elif custom_id == "settings_page_2":
      await self.settings_page_2(interaction)

    # settings_3
    elif custom_id == "settings_page_3":
      await self.on_page_refresh_check_permissions(interaction, "pticket")
      await self.settings_page_3(interaction)

    # settings_panel_config
    elif custom_id == "settings_panel_config":
      await self.on_page_refresh_check_permissions(interaction, "pticket", panel_config=True)
      await self.settings_panel_config(interaction)

    # Ticket作成用ボタンの場合
    elif custom_id == "settings_select_pticket_button_channel":
      channel, error_embed = await self.on_channel_select_check_permissions(interaction, button_channel=True)
      if error_embed:
        await interaction.response.send_message(embed=error_embed, ephemeral=True)
        await self.settings_panel_config(interaction, error=True, value=interaction.message.embeds[1].description)
        return
      else:
        if channel:
          if not channel.permissions_for(interaction.user).manage_channels:
            embed=await error.generate(code="1-4-02", additional_desc=channel.mention)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.settings_panel_config(interaction, error=True, value=interaction.message.embeds[1].description)
            return

        data = await self.get_data(interaction, type="pticket")
        data["report_button_channel"] = channel.id if channel else None
        await self.save_data(interaction, data, "pticket")
        await self.settings_panel_config(interaction, value=interaction.message.embeds[1].description)

    # チャンネル, ロールが選ばれた（選択解除された）場合
    elif "settings_select_" in custom_id:
      embed = interaction.message.embeds[0]

      # channelの場合 -> そのチャンネルのチャンネル管理権限があるか判定
      if "channel" in custom_id:
        if interaction.data["values"]:
          channel = interaction.guild.get_channel(int(interaction.data["values"][0]))
          if not channel.permissions_for(interaction.user).manage_channels:
            embed=await error.generate(code="1-4-03", additional_desc=channel.mention)

            await interaction.response.send_message(embed=embed, ephemeral=True)
            if "report" in custom_id:
              await self.settings_page_2(interaction, error=True)
            else:
              await self.settings_page_3(interaction, error=True)

            return

      # Report設定の場合
      if "report" in custom_id:
        data = await self.get_data(interaction, type="report")

        # Report送信チャンネル設定の場合
        if custom_id == "settings_select_report_channel":
          channel, error_embed = await self.on_channel_select_check_permissions(interaction)
          if error_embed:
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            await self.settings_page_2(interaction, error=True)
            return
          else:
            data["report_send_channel"] = channel.id if channel else None
        # Report送信時メンションロール設定の場合
        else:
          data["mention_role"] = int(interaction.data["values"][0]) if interaction.data["values"] else None

        await self.save_data(interaction, data, "report")
        await self.settings_page_2(interaction)

      # Ticket設定の場合
      else:
        data = await self.get_data(interaction, type="pticket")

        # Ticket送信チャンネル設定の場合
        if custom_id == "settings_select_pticket_channel":
          channel, error_embed = await self.on_channel_select_check_permissions(interaction)
          if error_embed:
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            await self.settings_page_3(interaction, error=True)
            return
          else:
            data["report_send_channel"] = channel.id if channel else None
        # Ticket作成時メンションロールの場合
        elif custom_id == "settings_select_pticket_mention_role":
          data["mention_role"] = int(interaction.data["values"][0]) if interaction.data["values"] else None

        await self.save_data(interaction, data, "pticket")
        await self.settings_page_3(interaction)


    # 保存して終了ボタン
    elif custom_id == "settings_final":
      await self.settings_final(interaction)


    # 確定ボタンを押したとき
    elif interaction.data["custom_id"] == "settings_confirm_private_ticket":
      view = discord.ui.View()
      button_0 = discord.ui.Button(label="匿名Ticket", emoji=EMOJI_DICT["new_label"], custom_id=f"private_ticket", style=discord.ButtonStyle.primary, disabled=False, row=0)
      view.add_item(button_0)

      # フィールド, フッターを消す
      embed = interaction.message.embeds[1]
      embed.remove_field(0)
      embed.set_footer(text=None)

      # 送信する
      pticket_data = await self.get_data(interaction, type="pticket")
      msg = await interaction.guild.get_channel(pticket_data["report_button_channel"]).send(embed=embed, view=view)

      await self.settings_final(interaction)


    # 編集ボタンを押した場合
    elif interaction.data["custom_id"] == "edit_private_ticket":
      modal = EditPrivateModal(self.bot, interaction.message)
      await interaction.response.send_modal(modal)


    # パネル設置しないを押した場合
    elif interaction.data["custom_id"] == "settings_delete_private_ticket":
      await self.settings_final(interaction)


  # チャンネル選択時の閲覧権限確認
  async def on_channel_select_check_permissions(self, interaction:discord.Interaction, button_channel:bool=False):
    if interaction.data["values"]:
      channel = interaction.guild.get_channel(int(interaction.data["values"][0]))

      permission_l = []
      cannot = False
      bot_member = interaction.guild.me

      if channel.permissions_for(bot_member).read_messages:
        permission_l.append(":white_check_mark:メッセージを見る")
      else:
        permission_l.append(":x:メッセージを見る")
        cannot = True

      if channel.permissions_for(bot_member).send_messages:
        permission_l.append(":white_check_mark:メッセージを送信")
      else:
        permission_l.append(":x:メッセージを送信")
        cannot = True

      # ボタン設置ちゃんねるのときは確認しない
      if not button_channel:
        if channel.permissions_for(bot_member).create_public_threads:
          permission_l.append(":white_check_mark:公開スレッドの作成")
        else:
          permission_l.append(":x:公開スレッドの作成")
          cannot = True

      if cannot:
        embed=await error.generate(code="1-4-04", additional_desc=f"{channel.mention}\n\n- " + "\n- ".join(permission_l))
        return channel, embed
      else:
        return channel, None

    else:
      return None, None

  # ページ更新時にチャンネル権限を確認する
  # 権限が不足していたら、表示前に自動でチャンネル設定を削除する
  async def on_page_refresh_check_permissions(self, interaction:discord.Interaction, case_type:str, panel_config:bool=None):
    data = await self.get_data(interaction, type=case_type)
    key = "report_button_channel" if panel_config else "report_send_channel"
    channel_id = data.get(key)

    if not channel_id:
      return

    bot_member = interaction.guild.me
    channel = self.bot.get_channel(channel_id)
    permissions = channel.permissions_for(bot_member)

    # 一つでも権限が不足していた場合
    # panel_configがNoneのときはcreate_public_threadsがなくてもOK
    issufficient_permissions = (
      not permissions.read_messages or
      not permissions.send_messages or
      (not permissions.create_public_threads and not panel_config)
    )

    if issufficient_permissions:
      data[key] = None
      await self.save_data(interaction, data, type=case_type)


# パネル編集
class EditPrivateModal(discord.ui.Modal):
  def __init__(self, bot, msg):
    super().__init__(title=f'匿名Ticket開始パネル 編集モーダル')
    self.bot = bot
    self.msg = msg

    self.private_ticket_msg = discord.ui.TextInput(
      label="パネルに表示する内容を入力してください。",
      style=discord.TextStyle.long,
      default=msg.embeds[1].description,
      required=True,
      row=0
    )
    self.add_item(self.private_ticket_msg)

  async def on_submit(self, interaction: discord.Interaction):
    # 編集パネルの変更
    settings = Settings(self.bot)
    await settings.settings_panel_config(interaction, value=self.private_ticket_msg.value)



async def setup(bot):
  await bot.add_cog(Settings(bot))