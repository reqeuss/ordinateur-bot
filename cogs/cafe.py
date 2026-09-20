import discord, random
from discord import app_commands
from discord.ext import commands

class Cafe(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="coffee",description="Commander un café.")
    async def coffee(self,interaction):
        u=await self.bot.db.get_user(interaction.guild.id,interaction.user.id)
        price=50
        if u["cookies"]<price:return await interaction.response.send_message("❌ Un café coûte 50 🍪.",ephemeral=True)
        await self.bot.db.change_money(interaction.guild.id,interaction.user.id,-price)
        await self.bot.db.add_item(interaction.guild.id,interaction.user.id,"cafe")
        await interaction.response.send_message("☕ Ton café arrive ! **-50 🍪**")
    @app_commands.command(name="menu",description="Voir le menu du café.")
    async def menu(self,interaction):
        await interaction.response.send_message(embed=discord.Embed(title="☕ Menu du Café Virtuel",
            description="☕ Café — 50 🍪\n🥐 Croissant — 75 🍪\n🍰 Gâteau — 120 🍪\n🍩 Donut — 100 🍪\n🧋 Bubble Tea — 150 🍪",
            color=discord.Color.orange()))
    @app_commands.command(name="cookie",description="Recevoir un message Cookie.")
    async def cookie(self,interaction):
        await interaction.response.send_message(random.choice(["🍪 Un cookie tout chaud !","🍪 Le chef t'offre un Cookie !","☕🍪 Pause goûter !"]))
    @app_commands.command(name="barista",description="Phrase aléatoire de barista.")
    async def barista(self,interaction):
        await interaction.response.send_message(random.choice(["☕ Votre café est prêt !","🥐 La fournée sort du four !","🧋 Bubble Tea en préparation !"]))
    @app_commands.command(name="order",description="Passer une commande au café.")
    async def order(self,interaction,item:str):
        await interaction.response.send_message(f"🧾 Commande enregistrée : **{item}**. Un serveur arrive !")
    @app_commands.command(name="review",description="Laisser une note au café.")
    async def review(self,interaction,rating:app_commands.Range[int,1,5],text:str="Sans commentaire"):
        await interaction.response.send_message(f"⭐ Note : **{rating}/5**\n💬 {text}")
    @app_commands.command(name="fortune",description="Obtenir une prédiction du café.")
    async def fortune(self,interaction):
        await interaction.response.send_message("🔮 "+random.choice(["Un gros bonus de Cookies arrive.","Ton prochain café sera légendaire.","Une surprise t'attend dans le serveur.","Ton niveau va bientôt monter !"]))
    @app_commands.command(name="coffeequote",description="Citation du café.")
    async def coffeequote(self,interaction):
        await interaction.response.send_message("☕ *« Un bon café, et on repart. »*")
    @app_commands.command(name="staffmenu",description="Menu réservé au staff.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def staffmenu(self,interaction):
        await interaction.response.send_message("🛡️ Staff : `/announce`, `/giveaway`, `/warn`, `/ban`, `/ticketsetup`, `/setmodlog`…",ephemeral=True)

async def setup(bot): await bot.add_cog(Cafe(bot))
