import os


def get_cogs() -> list[str]:
  cog_list = []

  for category in os.listdir("cogs"):
    if category == "dev" or category.startswith("_"):
      continue

    category_path = os.path.join("cogs", category)
    if not os.path.isdir(category_path):
      continue

    for file in os.listdir(category_path):
      if not file.startswith("_"):
        cog_list.append(f"cogs.{category}.{file[:-3]}")

  return cog_list

def get_dev_cogs() -> list[str]:
  dev_cog_list = []
  files = os.listdir("cogs/dev")
  for file in files:
    if not file.startswith("_"):
      dev_cog_list.append(f"cogs.dev.{file[:-3]}")

  return dev_cog_list
