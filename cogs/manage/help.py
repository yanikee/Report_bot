from discord.ext import commands
from discord import app_commands, ui
import discord

from modules import cogs



dev_cog_list = cogs.get_dev_cogs()

class Help(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="help", description='helpコマンドです')
  async def help(self, interaction: discord.Interaction):
    embed = discord.Embed(
      title="Help! (1/4)",
      description="このbotの2つの機能！\n\n"
                  "## 1. __Report機能__\n"
                  "不適切なメッセージなどを、サーバー管理者に簡単に報告できる機能\n"
                  "## 2. __匿名Ticket機能__\n"
                  "『Ticket Tool』の匿名版の様な機能",
      color=0xffe7ab,
    )

    view = ui.View()
    button_0 = ui.Button(label="まず始めに！（設定方法）", emoji="⚙️", custom_id=f"quickstart", style=discord.ButtonStyle.primary, row=0)
    button_1 = ui.Button(label="使い方を知りたい！", emoji="✊", custom_id=f"how_to_use", style=discord.ButtonStyle.green, row=1)
    button_2 = ui.Button(label="その他", emoji="💪", custom_id=f"others", style=discord.ButtonStyle.gray, row=1)
    view.add_item(button_0)
    view.add_item(button_1)
    view.add_item(button_2)

    if await self.bot.is_owner(interaction.user):
      button_3 = ui.Button(label="dev_mode", emoji="🥟", custom_id=f"dev_mode", style=discord.ButtonStyle.red, row=2)
      view.add_item(button_3)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)



  @commands.Cog.listener()
  async def on_interaction(self, interaction: discord.Interaction):
    if not interaction.data:
      return

    custom_id = interaction.data.get("custom_id", "")
    if not custom_id in ["dev_mode", "quickstart", "how_to_use", "others"]:
      return

    if custom_id == "dev_mode":
      for dev_cog in dev_cog_list:
        if dev_cog in self.bot.extensions:
          await self.bot.unload_extension(dev_cog)
          print(f"アンロード完了：{dev_cog}")
          msg = "アンロード完了"
        else:
          await self.bot.load_extension(dev_cog)
          print(f"ロード完了：{dev_cog}")
          msg = "ロード完了"

      await interaction.response.send_message(msg, ephemeral=True)
      await self.bot.tree.sync()


    elif custom_id == "quickstart":
      embed=discord.Embed(
        title="Help! (2/4)",
        description="## まず始めに！(設定方法)\n"
                    "__## `/settings` を実行__"
                    "Report機能，匿名Ticket機能の設定をします",
        color=0xffe7ab,
      )
      await interaction.response.edit_message(embed=embed)

    elif custom_id == "how_to_use":
      embed=discord.Embed(
        title="Help! (3/4)",
        description="# 使い方を知りたい！\n"
                    "## Report機能\n"
                    "1. 報告したいメッセージを右クリック\n"
                    "2. 「アプリ」\n"
                    "3. 【サーバー管理者に報告】\n"
                    "## 匿名Ticket機能\n"
                    "1. 匿名Ticketボタンを押すだけ！\n"
                    "  - ボタンが存在しない場合は、サーバー管理者さんに聞いてみて",
        color=0xffe7ab,
      )
      await interaction.response.edit_message(embed=embed)

    elif custom_id == "others":
      embed=discord.Embed(
        title="Help! (4/4)",
        description="## その他\n"
                    "## `/block <block_type: [選択]>`\n"
                    "- 報告者による返信をブロックしたい場合に使用します\n"
                    "- 匿名Report/Ticketのスレッド内で実行してください\n"
                    "## クールダウンについて\n"
                    "- botの負荷軽減, 悪用を防ぐためにクールダウンを導入しています\n"
                    "- 以下の機能は30秒に1度まで利用できます\n"
                    "  - 【！サーバー管理者に報告】\n"
                    "  - Ticket開始ボタン\n"
                    "  - DMからサーバー管理者への返信",
        color=0xffe7ab,
      )
      await interaction.response.edit_message(embed=embed)



async def setup(bot):
  await bot.add_cog(Help(bot))