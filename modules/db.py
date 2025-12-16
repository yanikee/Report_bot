from typing import TypedDict, Literal, cast
from supabase import create_client, Client

from const import SUPABASE_URL, SUPABASE_KEY



class GuildSettings(TypedDict):
  guild_id: int
  report_channel_id: int | None
  report_mention_role_id: int | None
  report_count: int
  ticket_channel_id: int | None
  ticket_button_channel_id: int | None
  ticket_mention_role_id: int | None
  ticket_count: int
  created_at: str

class Threads(TypedDict):
  thread_id: int
  guild_id: int
  user_id: int
  case_type: Literal["report", "ticket"]
  is_blocked: bool
  created_at: str

class BlockedUsers(TypedDict):
  id: int
  guild_id: int
  user_id: int
  created_at: str



class DB:
  def __init__(self):
    self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

  # 設定の取得
  async def get_guild_settings(self, guild_id: int) -> GuildSettings | None:
    res = self.supabase.table("guild_settings").select("*").eq("guild_id", guild_id).execute()
    return cast(GuildSettings, res.data[0]) if res.data else None

    # 設定の保存/更新
  async def upsert_guild_settings(self, data: dict):
    self.supabase.table("guild_settings").upsert(data).execute()

  # スレッドの取得
  async def get_thread(self, thread_id: int) -> Threads | None:
    res = self.supabase.table("threads").select("*").eq("thread_id", thread_id).execute()
    return cast(Threads, res.data[0]) if res.data else None

  # 新規スレッド作成時
  async def create_thread_entry(
    self, thread_id: int, guild_id: int, user_id: int, case_type: Literal["report", "ticket"]
  ):
    data = {
      "thread_id": thread_id,
      "guild_id": guild_id,
      "user_id": user_id,
      "case_type": case_type
    }
    self.supabase.table("threads").insert(data).execute()

  # ブロック状態のトグル (サーバー全体)
  # 戻り値: True(ブロックした), False(解除した)
  async def toggle_guild_block(self, guild_id: int, user_id: int) -> bool:
    res = self.supabase.table("blocked_users").select("*").eq("guild_id", guild_id).eq("user_id", user_id).execute()

    if res.data:
      # 既にブロックされている場合は削除
      self.supabase.table("blocked_users").delete().eq("guild_id", guild_id).eq("user_id", user_id).execute()
      return False
    else:
      # ブロック追加
      self.supabase.table("blocked_users").insert({"guild_id": guild_id, "user_id": user_id}).execute()
      return True

  # スレッド内ブロックのトグル
  # 戻り値: True(ブロックした), False(解除した), None(スレッドが見つからない)
  async def toggle_thread_block(self, thread_id: int) -> bool | None:
    current = await self.get_thread(thread_id)
    if not current:
      return None

    new_status = not current["is_blocked"]
    self.supabase.table("threads").update({"is_blocked": new_status}).eq("thread_id", thread_id).execute()
    return new_status