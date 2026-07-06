from typing import Literal, NotRequired, TypedDict


class _GuildSettingsBase(TypedDict):
    guild_id: int
    report_channel_id: int | None
    report_mention_role_id: int | None
    ticket_channel_id: int | None
    ticket_button_channel_id: int | None
    ticket_mention_role_id: int | None

class GuildSettingsWrite(_GuildSettingsBase):
    report_count: NotRequired[int]
    ticket_count: NotRequired[int]
    created_at: NotRequired[str]

class GuildSettings(_GuildSettingsBase):
    report_count: int
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
