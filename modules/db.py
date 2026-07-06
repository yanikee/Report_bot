from typing import Any, Literal, cast

from supabase import acreate_client

from const import SUPABASE_KEY, SUPABASE_URL

from .types import GuildSettings, GuildSettingsWrite, Threads


class DB:
  def __init__(self):
    self._client = None

  async def get_client(self):
    if not self._client:
      self._client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)

    return self._client

  # 設定の取得
  async def get_guild_settings(self, guild_id: int) -> GuildSettings | None:
    supabase = await self.get_client()

    res = await supabase.table("guild_settings")\
      .select("*")\
      .eq("guild_id", guild_id)\
      .execute()

    return cast(GuildSettings, res.data[0]) if res.data else None

    # 設定の保存/更新
  async def upsert_guild_settings(self, data: GuildSettingsWrite | GuildSettings):
    supabase = await self.get_client()

    await supabase.table("guild_settings")\
      .upsert(cast(dict[str, Any], data))\
      .execute()

  async def create_guild_settings(self, guild_id: int) -> GuildSettings:
    new_data: GuildSettingsWrite = {
      "guild_id": guild_id,
      "report_channel_id": None,
      "report_mention_role_id": None,
      "report_count": 0,
      "ticket_channel_id": None,
      "ticket_button_channel_id": None,
      "ticket_mention_role_id": None,
      "ticket_count": 0,
    }

    await self.upsert_guild_settings(new_data)
    data = await self.get_guild_settings(guild_id)
    return cast(GuildSettings, data)

  # スレッドの取得
  async def get_thread(self, thread_id: int) -> Threads | None:
    supabase = await self.get_client()

    res = await supabase.table("threads")\
      .select("*")\
      .eq("thread_id", thread_id)\
      .execute()

    return cast(Threads, res.data[0]) if res.data else None

  # 新規スレッド作成時
  async def create_thread_entry(self, thread_id: int, guild_id: int, user_id: int, case_type: Literal["report", "ticket"]):
    supabase = await self.get_client()

    data = {
      "thread_id": thread_id,
      "guild_id": guild_id,
      "user_id": user_id,
      "case_type": case_type
    }
    await supabase.table("threads")\
      .insert(data)\
      .execute()

  async def is_guild_blocked(self, guild_id: int, user_id: int) -> bool:
    supabase = await self.get_client()

    res = await supabase.table("blocked_users")\
      .select("*")\
      .eq("guild_id", guild_id)\
      .eq("user_id", user_id)\
      .maybe_single()\
      .execute()

    return res is not None

  # ブロック状態のトグル (サーバー全体)
  # 戻り値: True(ブロックした), False(解除した)
  async def toggle_guild_block(self, guild_id: int, user_id: int) -> bool:
    supabase = await self.get_client()

    res = await supabase.table("blocked_users")\
      .select("*")\
      .eq("guild_id", guild_id)\
      .eq("user_id", user_id)\
      .execute()

    if res.data:
      # 既にブロックされている場合は削除
      await supabase.table("blocked_users")\
        .delete()\
        .eq("guild_id", guild_id)\
        .eq("user_id", user_id)\
        .execute()

      return False

    else:
      # ブロック追加
      await supabase.table("blocked_users")\
        .insert({ "guild_id": guild_id, "user_id": user_id })\
        .execute()
      return True

  # スレッド内ブロックのトグル
  # 戻り値: True(ブロックした), False(解除した), None(スレッドが見つからない)
  async def toggle_thread_block(self, thread_id: int) -> bool | None:
    supabase = await self.get_client()

    current = await self.get_thread(thread_id)
    if not current:
      return None

    new_status = not current["is_blocked"]
    await supabase.table("threads")\
      .update({ "is_blocked": new_status })\
      .eq("thread_id", thread_id)\
      .execute()

    return new_status
