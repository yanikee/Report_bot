from discord import ui
import discord

import datetime
from const import EMOJI_DICT



def user_cooldown(user_id: int, user_cooldowns: dict, rate:int=30):
  current_time = int(datetime.datetime.now().timestamp())

  if str(user_id) in user_cooldowns:
    retry_after = user_cooldowns[str(user_id)] - current_time

    if retry_after > 0:
      retry_minute = int(retry_after) // 60
      retry_second = int(retry_after) % 60
      embed = discord.Embed(
        title=f"Cooldown",
        description=f"クールダウン中です。\nあと{retry_minute}分{retry_second}秒お待ち下さい。",
        color=0xF2E700,
      )
      return embed, user_cooldowns

    else:
      user_cooldowns.pop(str(user_id))

  user_cooldowns[str(user_id)] = current_time + rate
  return None, user_cooldowns



async def get_reply_view(content: str | None = None, values: list[discord.Attachment] | None = None) -> ui.LayoutView:
  view = ui.LayoutView()

  container = ui.Container(accent_color=0x95FFA1)
  container.add_item(ui.TextDisplay("### 返信内容"))
  if content:
    container.add_item(ui.TextDisplay(content))
    disabled = False
  else:
    container.add_item(ui.TextDisplay("下のボタンから編集してください。"))
    disabled = True
  view.add_item(container)

  if values:
    container.add_item(ui.TextDisplay(f"### 添付ファイル"))
    for file in values:
      container.add_item(ui.File(await file.to_file()))


  row = ui.ActionRow()
  row.add_item(ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"report_edit_reply", style=discord.ButtonStyle.primary))
  row.add_item(ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"report_send", style=discord.ButtonStyle.red, disabled=disabled))
  view.add_item(row)

  return view