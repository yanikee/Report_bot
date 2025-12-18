from dotenv import load_dotenv
import os


load_dotenv(override=True)

EMOJI_DICT = {
  "check": "<:check:1451053158880116798>",
  "add": "<:add:1335909447687733300>",
  "arrow_forward": "<:arrow_forward:1450452012566315120>",
  "arrow_back": "<:arrow_back:1335907900920565780>",
  "new_label": "<:new_label:1335916826114392126>",
  "person_alert": "<:person_alert:1335916869714055209>",
  "reply": "<:reply:1335932856899342397>",
  "report": "<:report:1335916894775021579>",
  "edit": "<:edit:1335899691983831070>",
  "send": "<:send:1335899659553738815>",
  "upload_file": "<:upload_file:1335899677186326559>",
  "delete": "<:delete:1335899643049017355>",
}

TOKEN = os.environ.get("TOKEN", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")