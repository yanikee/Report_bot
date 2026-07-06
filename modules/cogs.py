import os


def get_cogs() -> list[str]:
  cog_list = []

  path_l = ["manage", "report", "pticket"]
  for path in path_l:
    files = os.listdir(f"cogs/{path}")
    for file in files:
      if not file.startswith("_"):
        cog_list.append(f"cogs.{path}.{file[:-3]}")
  return cog_list

def get_dev_cogs() -> list[str]:
  dev_cog_list = []
  files = os.listdir(f"cogs/dev")
  for file in files:
    if not file.startswith("_"):
      dev_cog_list.append(f"cogs.dev.{file[:-3]}")

  return dev_cog_list