import discord



async def send_error(msg: str, interaction: discord.Interaction | None = None, channel: discord.TextChannel | discord.Thread | discord.DMChannel | None = None, followup: bool = False):
  description = f"{msg}\n\n- サポートサーバーは[こちら](https://discord.gg/djQHvM6PtE)"

  embed=discord.Embed(
    title=f"ERROR",
    description=description,
    color=0xF2E700,
  )

  if interaction:
    if followup:
      await interaction.followup.send(embed=embed, ephemeral=True)
    else:
      await interaction.response.send_message(embed=embed, ephemeral=True)

  if channel:
    await channel.send(embed=embed)