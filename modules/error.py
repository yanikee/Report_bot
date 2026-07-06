from discord import DMChannel, Embed, Interaction, TextChannel, Thread


async def send_error(msg: str, interaction: Interaction | None = None, channel: TextChannel | Thread | DMChannel | None = None, followup: bool = False):
  description = f"# ERROR\n{msg}\n\n- サポートサーバーは[こちら](https://gg/djQHvM6PtE)"
  embed = Embed(
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
