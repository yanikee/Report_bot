import discord



async def send_error(interaction: discord.Interaction, msg: str, followup: bool = False):
  description = f"{msg}\n\n- サポートサーバーは[こちら](https://discord.gg/djQHvM6PtE)"

  embed=discord.Embed(
    title=f"ERROR",
    description=description,
    color=0xF2E700,
  )

  if followup:
    await interaction.followup.send(embed=embed, ephemeral=True)
  else:
    await interaction.response.send_message(embed=embed, ephemeral=True)
