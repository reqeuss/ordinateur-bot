import discord
from discord import app_commands
from discord.ext import commands

class Server(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="serverinfo",description="Informations du serveur.")
    async def serverinfo(self,interaction):
        g=interaction.guild
        await interaction.response.send_message(embed=discord.Embed(
            title=f"🏠 {g.name}",description=f"👥 Membres : **{g.member_count}**\n📺 Salons : **{len(g.channels)}**\n🎭 Rôles : **{len(g.roles)}**\n🆔 `{g.id}`",color=discord.Color.blurple()))
    @app_commands.command(name="userinfo",description="Informations sur un membre.")
    async def userinfo(self,interaction,member:discord.Member=None):
        m=member or interaction.user
        await interaction.response.send_message(embed=discord.Embed(title=f"👤 {m}",description=f"ID : `{m.id}`\nCompte créé : <t:{int(m.created_at.timestamp())}:D>\nEntré : <t:{int(m.joined_at.timestamp())}:D>"))
    @app_commands.command(name="avatar",description="Afficher un avatar.")
    async def avatar(self,interaction,member:discord.Member=None):
        m=member or interaction.user
        await interaction.response.send_message(m.display_avatar.url)
    @app_commands.command(name="banner",description="Afficher la bannière d'un utilisateur.")
    async def banner(self,interaction,member:discord.Member=None):
        m=member or interaction.user
        u=await self.bot.fetch_user(m.id)
        await interaction.response.send_message(u.banner.url if u.banner else "❌ Pas de bannière.")
    @app_commands.command(name="roles",description="Lister les rôles du serveur.")
    async def roles(self,interaction):
        roles=[r.mention for r in reversed(interaction.guild.roles) if r.name!="@everyone"]
        await interaction.response.send_message("🎭 "+(" ".join(roles)[:1900] or "Aucun rôle."))
    @app_commands.command(name="membercount",description="Nombre de membres.")
    async def membercount(self,interaction):
        await interaction.response.send_message(f"👥 **{interaction.guild.member_count}** membres.")
    @app_commands.command(name="say",description="Faire parler le bot.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def say(self,interaction,text:str):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.send(text)
        await interaction.followup.send("✅ Envoyé.",ephemeral=True)
    @app_commands.command(name="announce",description="Créer une annonce.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def announce(self,interaction,title:str,text:str):
        e=discord.Embed(title="📢 "+title,description=text,color=discord.Color.blurple())
        e.set_footer(text=f"Annonce par {interaction.user.display_name}")
        await interaction.channel.send(embed=e)
        await interaction.response.send_message("📢 Annonce publiée.",ephemeral=True)
    @app_commands.command(name="embed",description="Envoyer un embed simple.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def embed(self,interaction,title:str,text:str):
        await interaction.channel.send(embed=discord.Embed(title=title,description=text,color=discord.Color.blurple()))
        await interaction.response.send_message("✅ Embed envoyé.",ephemeral=True)
    @app_commands.command(name="poll",description="Créer un sondage.")
    async def poll(self,interaction,question:str):
        msg=await interaction.channel.send(embed=discord.Embed(title="📊 Sondage",description=question))
        await msg.add_reaction("👍"); await msg.add_reaction("👎")
        await interaction.response.send_message("📊 Sondage créé.",ephemeral=True)
    @app_commands.command(name="suggest",description="Faire une suggestion.")
    async def suggest(self,interaction,text:str):
        settings=await self.bot.db.get_settings(interaction.guild.id)
        ch=interaction.guild.get_channel(settings["announcements_channel"]) if settings and settings["announcements_channel"] else interaction.channel
        await ch.send(embed=discord.Embed(title="💡 Suggestion",description=text).set_footer(text=str(interaction.user)))
        await interaction.response.send_message("💡 Suggestion envoyée.",ephemeral=True)
    @app_commands.command(name="help",description="Afficher toutes les commandes.")
    async def help(self,interaction):
        groups={
            "☕ Café":"`/coffee` `/menu` `/order` `/review` `/barista` `/cookie` `/fortune`",
            "🍪 Économie":"`/balance` `/daily` `/work` `/timer` `/shop` `/buy` `/inventory` `/use` `/pay` `/deposit` `/withdraw` `/leaderboard` `/economy` `/beg` `/crime` `/rob` `/freecoffee`",
            "⭐ XP":"`/profile` `/rank` `/level` `/levelboard` `/setlevel` `/setxp`",
            "🛡️ Modération":"`/warn` `/warnings` `/clearwarnings` `/clear` `/purgeuser` `/cleanup` `/kick` `/ban` `/unban` `/timeout` `/untimeout` `/nick` `/roleadd` `/roleremove` `/rolecreate` `/roledelete` `/slowmode` `/lock` `/unlock` `/serverlockdown` `/serverunlock` `/modlogs` `/automod`",
            "🎫 Serveur":"`/ticket` `/close` `/claim` `/partnership` `/serverinfo` `/userinfo` `/avatar` `/banner` `/roles` `/membercount` `/announce` `/embed` `/poll` `/suggest` `/say`",
            "🎉 Giveaways":"`/giveaway` `/reroll` `/giveawayend`",
            "🤖 Autres":"`/ping` `&537UP` `/flip` `/dice` `/rps` `/random` `/8ball` `/rate` `/choose` `/cookiegift`"
        }
        desc="\n\n".join(f"**{k}**\n{v}" for k,v in groups.items())
        await interaction.response.send_message(embed=discord.Embed(title="🤖 Commandes d’Ordinateur",description=desc,color=discord.Color.blurple()))

async def setup(bot): await bot.add_cog(Server(bot))
