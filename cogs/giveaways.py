import discord, time, random, re
from discord import app_commands
from discord.ext import commands

class GiveawayButton(discord.ui.View):
    def __init__(self,cog,message_id):
        super().__init__(timeout=None); self.cog=cog; self.message_id=message_id
    @discord.ui.button(label="Participer",emoji="🎉",style=discord.ButtonStyle.success)
    async def enter(self,interaction,button):
        try:
            msg=interaction.message
            await msg.add_reaction("🎉")
            await interaction.response.send_message("🎉 Participation ajoutée !",ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("❌ Impossible de participer.",ephemeral=True)

class Giveaways(commands.Cog):
    def __init__(self,bot): self.bot=bot
    async def finish_giveaway(self,message_id):
        rows=await self.bot.db.active_giveaways()
        row=next((r for r in rows if r["message_id"]==message_id),None)
        if not row:return
        ch=self.bot.get_channel(row["channel_id"])
        if not ch:
            await self.bot.db.end_giveaway(message_id); return
        try: msg=await ch.fetch_message(message_id)
        except:
            await self.bot.db.end_giveaway(message_id); return
        users=[u async for u in msg.reactions[0].users() if not u.bot] if msg.reactions else []
        if not users:
            text="😢 Aucun participant."
        else:
            winners=random.sample(users,min(row["winners"],len(users)))
            text="🎉 Gagnants : "+", ".join(u.mention for u in winners)+f"\n🎁 Prix : **{row['prize']}**"
        await msg.edit(embed=discord.Embed(title="🎉 GIVEAWAY TERMINÉ",description=text,color=discord.Color.dark_gold()),view=None)
        await ch.send(text)
        await self.bot.db.end_giveaway(message_id)

    @app_commands.command(name="giveaway",description="Créer un giveaway.")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(duration="Durée comme 10m, 2h, 1d",prize="Prix",winners="Nombre de gagnants")
    async def giveaway(self,interaction,duration:str,prize:str,winners:app_commands.Range[int,1,20]=1):
        m=re.fullmatch(r"\s*(\d+)\s*([smhd])\s*",duration.lower())
        if not m:return await interaction.response.send_message("❌ Durée invalide. Ex: `10m`, `2h`, `1d`.",ephemeral=True)
        n=int(m.group(1)); unit=m.group(2); mult={"s":1,"m":60,"h":3600,"d":86400}[unit]
        seconds=n*mult
        if seconds<10 or seconds>604800:return await interaction.response.send_message("❌ Durée : 10 secondes à 7 jours.",ephemeral=True)
        end=int(time.time()+seconds)
        e=discord.Embed(title="🎉 GIVEAWAY",description=f"🎁 Prix : **{prize}**\n👑 Gagnants : **{winners}**\n⏰ Fin : <t:{end}:R>\n\nClique sur **Participer** !",color=discord.Color.gold())
        e.set_footer(text=f"Créé par {interaction.user.display_name}")
        await interaction.response.defer()
        msg=await interaction.channel.send(embed=e)
        await msg.add_reaction("🎉")
        await self.bot.db.save_giveaway((msg.id,interaction.guild.id,interaction.channel.id,prize,winners,end,0))
        await msg.edit(view=GiveawayButton(self,msg.id))
        await interaction.followup.send("🎉 Giveaway créé.",ephemeral=True)

    @app_commands.command(name="giveawayend",description="Terminer immédiatement un giveaway.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveawayend(self,interaction,message_id:str):
        try: mid=int(message_id)
        except: return await interaction.response.send_message("❌ ID invalide.",ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        await self.finish_giveaway(mid)
        await interaction.followup.send("🎉 Giveaway terminé.",ephemeral=True)

    @app_commands.command(name="reroll",description="Reroll un giveaway terminé.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reroll(self,interaction,message_id:str):
        try: mid=int(message_id); msg=await interaction.channel.fetch_message(mid)
        except: return await interaction.response.send_message("❌ Message introuvable.",ephemeral=True)
        users=[u async for u in msg.reactions[0].users() if not u.bot] if msg.reactions else []
        if not users:return await interaction.response.send_message("❌ Aucun participant.",ephemeral=True)
        winner=random.choice(users)
        await interaction.response.send_message(f"🔄 Nouveau gagnant : {winner.mention} 🎉")

async def setup(bot): await bot.add_cog(Giveaways(bot))
