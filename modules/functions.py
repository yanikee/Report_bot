import datetime
import io
from typing import Literal

import aiohttp
from discord import (
  Attachment,
  ButtonStyle,
  Embed,
  File,
  Message,
  SelectOption,
  UnfurledMediaItem,
  components,
  ui,
)

from const import EMOJI_DICT


def user_cooldown(user_id: int, user_cooldowns: dict, rate: int=30):
  current_time = int(datetime.datetime.now().timestamp())

  if str(user_id) in user_cooldowns:
    retry_after = user_cooldowns[str(user_id)] - current_time

    if retry_after > 0:
      retry_minute = int(retry_after) // 60
      retry_second = int(retry_after) % 60
      embed = Embed(
        title="Cooldown",
        description=f"クールダウン中です\nあと{retry_minute}分{retry_second}秒お待ち下さい",
        color=0xF2E700,
      )
      return embed, user_cooldowns

    else:
      user_cooldowns.pop(str(user_id))

  user_cooldowns[str(user_id)] = current_time + rate
  return None, user_cooldowns



async def create_reply_view(
  case_type: Literal["report", "pticket"], content: str | None = None, values: list[Attachment | File] | None = None
) -> tuple[ui.LayoutView, list[File]]:
  view = ui.LayoutView()

  container = ui.Container(accent_color=0x95FFA1)
  container.add_item(ui.TextDisplay("## 返信内容"))
  if content:
    container.add_item(ui.TextDisplay(content, id=999))
    disabled = False
  else:
    container.add_item(ui.TextDisplay("下のボタンから編集してください", id=999))
    disabled = True

  files: list[File] = []
  if values:
    container.add_item(ui.TextDisplay("## 添付ファイル"))
    for value in values:
      if isinstance(value, Attachment):
        file = await value.to_file()
      else:
        file = value

      files.append(file)
      container.add_item(ui.File(file))

    row = ui.ActionRow()
    row.add_item(ui.Select(
      custom_id=f"{case_type}_file_delete",
      placeholder="削除したいファイルを選択",
      required=False,
      options=[SelectOption(
        label=file.filename,
      ) for file in files]
    ))
    container.add_item(row)

  view.add_item(container)

  row = ui.ActionRow()
  row.add_item(ui.Button(emoji=EMOJI_DICT["edit"], label="編集", custom_id=f"{case_type}_edit_reply", style=ButtonStyle.primary))
  row.add_item(ui.Button(emoji=EMOJI_DICT["send"], label="送信", custom_id=f"{case_type}_send", style=ButtonStyle.red, disabled=disabled))
  if not content and not files:
    row.add_item(ui.Button(emoji=EMOJI_DICT["delete"], label="もう返信しない", custom_id=f"{case_type}_cancel", style=ButtonStyle.gray))
  view.add_item(row)

  return view, files


def get_reply_view_data(msg: Message) -> tuple[str, list[UnfurledMediaItem]]:
  contents: list[str] = []
  medias: list[UnfurledMediaItem] = []

  for comp in msg.components:
    if isinstance(comp, components.Container):
      children = comp.children

      for child in children:
        if isinstance(child, components.TextDisplay) and child.id == 999:
          contents.append(child.content)

        if isinstance(child, components.FileComponent):
          medias.append(child.media)

  content = "\n".join(contents)
  return content, medias



async def get_files(medias: list[UnfurledMediaItem]) -> list[File]:
  files: list[File] = []
  async with aiohttp.ClientSession() as session:
    for item in medias:
      async with session.get(item.url) as resp:
        data = await resp.read()
        filename = item.url.split('/')[-1].split('?')[0]
        files.append(File(io.BytesIO(data), filename=filename))

  return files
