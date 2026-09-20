import time
import random
import discord
from discord import app_commands

def fmt_time(seconds: int):
    seconds = max(0, int(seconds))
    d, seconds = divmod(seconds, 86400)
    h, seconds = divmod(seconds, 3600)
    m, s = divmod(seconds, 60)
    parts = []
    if d: parts.append(f"{d}j")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s and not parts: parts.append(f"{s}s")
    return " ".join(parts) or "0s"

def cooldown_text(last, cooldown):
    remaining = int(cooldown - (time.time() - last))
    return None if remaining <= 0 else fmt_time(remaining)

def money(n):
    return f"{n:,}".replace(",", " ")

def is_admin(member):
    return member.guild_permissions.administrator

async def send_embed(interaction, title, description, ephemeral=False):
    await interaction.response.send_message(
        embed=discord.Embed(title=title, description=description, color=discord.Color.blurple()),
        ephemeral=ephemeral
    )

def item_price(item):
    prices = {
        "cafe": 50, "croissant": 75, "gateau": 120, "donut": 100,
        "bubbletea": 150, "mysterybox": 1000, "vipcard": 5000
    }
    return prices.get(item.lower())

def item_display(item):
    return {
        "cafe":"☕ Café", "croissant":"🥐 Croissant", "gateau":"🍰 Gâteau",
        "donut":"🍩 Donut", "bubbletea":"🧋 Bubble Tea",
        "mysterybox":"🎁 Mystery Box", "vipcard":"💳 Carte VIP"
    }.get(item.lower(), item)
