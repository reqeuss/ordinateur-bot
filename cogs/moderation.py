import discord, time
from discord import app_commands
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot): self.bot=bot

    async def log(self, guild, title, text):
        s=await self.bot.db.get_settings(guild.id)
        if s and s["modlog_channel"]:
            ch=guild.get_channel(s["modlog_channel"])
            if ch:
                try: await ch.send(embed=discord.Embed(title=title,description=text,color=discord.Color.orange()))
                except discord.HTTPException: pass

    @app_commands.command(name="warn", description="Avertir un membre.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction, member:discord.Member, reason:str="Aucune raison"):
        if member.bot: return await interaction.response.send_message("❌ Cible invalide.",ephemeral=True)
        case=await self.bot.db.add_warning(interaction.guild.id,member.id,interaction.user.id,reason,int(time.time()))
        await self.log(interaction.guild,"⚠️ Warn",f"Case #{case} — {member.mention}\nRaison : {reason}")
        await interaction.response.send_message(f"⚠️ {member.mention} averti. Case **#{case}**.")
    @app_commands.command(name="warnings",description="Voir les avertissements.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings(self,interaction,member:discord.Member):
        rows=await self.bot.db.get_warnings(interaction.guild.id,member.id)
        if not rows:return await interaction.response.send_message("✅ Aucun avertissement.")
        desc="\n".join(f"**#{r['id']}** — <@{r['moderator_id']}> — {r['reason']}" for r in rows[:20])
        await interaction.response.send_message(embed=discord.Embed(title=f"⚠️ Warnings de {member}",description=desc))
    @app_commands.command(name="clearwarnings",description="Effacer les warnings d'un membre.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def clearwarnings(self,interaction,member:discord.Member):
        await self.bot.db.clear_warnings(interaction.guild.id,member.id)
        await interaction.response.send_message(f"🧹 Warnings effacés pour {member.mention}.")
    @app_commands.command(name="clear",description="Supprimer des messages.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self,interaction,amount:app_commands.Range[int,1,100]):
        await interaction.response.defer(ephemeral=True)
        deleted=await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 **{len(deleted)}** messages supprimés.",ephemeral=True)
    @app_commands.command(name="purgeuser",description="Supprimer les messages d'un membre.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purgeuser(self,interaction,member:discord.Member,amount:app_commands.Range[int,1,100]):
        await interaction.response.defer(ephemeral=True)
        msgs=[m async for m in interaction.channel.history(limit=500) if m.author.id==member.id][:amount]
        if msgs: await interaction.channel.delete_messages(msgs)
        await interaction.followup.send(f"🧹 **{len(msgs)}** messages supprimés.",ephemeral=True)
    @app_commands.command(name="slowmode",description="Régler le slowmode.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self,interaction,seconds:app_commands.Range[int,0,21600]):
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"🐢 Slowmode : **{seconds}s**.")
    @app_commands.command(name="lock",description="Verrouiller le salon.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self,interaction):
        ow=interaction.channel.overwrites_for(interaction.guild.default_role); ow.send_messages=False
        await interaction.channel.set_permissions(interaction.guild.default_role,overwrite=ow)
        await interaction.response.send_message("🔒 Salon verrouillé.")
    @app_commands.command(name="unlock",description="Déverrouiller le salon.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self,interaction):
        ow=interaction.channel.overwrites_for(interaction.guild.default_role); ow.send_messages=None
        await interaction.channel.set_permissions(interaction.guild.default_role,overwrite=ow)
        await interaction.response.send_message("🔓 Salon déverrouillé.")
    @app_commands.command(name="kick",description="Expulser un membre.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self,interaction,member:discord.Member,reason:str="Aucune raison"):
        await member.kick(reason=reason); await self.log(interaction.guild,"👢 Kick",f"{member} — {reason}")
        await interaction.response.send_message(f"👢 {member.mention} expulsé.")
    @app_commands.command(name="ban",description="Bannir un membre.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self,interaction,member:discord.Member,reason:str="Aucune raison"):
        await member.ban(reason=reason); await self.log(interaction.guild,"🔨 Ban",f"{member} — {reason}")
        await interaction.response.send_message(f"🔨 {member.mention} banni.")
    @app_commands.command(name="unban",description="Débannir via ID.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self,interaction,user_id:str):
        try: uid=int(user_id)
        except: return await interaction.response.send_message("❌ ID invalide.",ephemeral=True)
        try:
            user=await self.bot.fetch_user(uid); await interaction.guild.unban(user)
            await interaction.response.send_message(f"🔓 {user} débanni.")
        except discord.HTTPException:
            await interaction.response.send_message("❌ Impossible de débannir cet utilisateur.",ephemeral=True)
    @app_commands.command(name="timeout",description="Timeout un membre.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self,interaction,member:discord.Member,minutes:app_commands.Range[int,1,40320],reason:str="Aucune raison"):
        await member.timeout(discord.utils.utcnow()+__import__('datetime').timedelta(minutes=minutes),reason=reason)
        await interaction.response.send_message(f"⏳ {member.mention} timeout pendant **{minutes} min**.")
    @app_commands.command(name="untimeout",description="Retirer le timeout.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self,interaction,member:discord.Member):
        await member.timeout(None); await interaction.response.send_message(f"🔓 Timeout retiré pour {member.mention}.")
    @app_commands.command(name="nick",description="Changer le pseudo.")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nick(self,interaction,member:discord.Member,nickname:str=""):
        await member.edit(nick=nickname or None); await interaction.response.send_message("✏️ Pseudo modifié.")
    @app_commands.command(name="roleadd",description="Ajouter un rôle.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def roleadd(self,interaction,member:discord.Member,role:discord.Role):
        await member.add_roles(role); await interaction.response.send_message(f"➕ {role.mention} ajouté à {member.mention}.")
    @app_commands.command(name="roleremove",description="Retirer un rôle.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def roleremove(self,interaction,member:discord.Member,role:discord.Role):
        await member.remove_roles(role); await interaction.response.send_message(f"➖ {role.mention} retiré de {member.mention}.")
    @app_commands.command(name="rolecreate",description="Créer un rôle.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rolecreate(self,interaction,name:str):
        role=await interaction.guild.create_role(name=name); await interaction.response.send_message(f"✅ Rôle créé : {role.mention}.")
    @app_commands.command(name="roledelete",description="Supprimer un rôle.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def roledelete(self,interaction,role:discord.Role):
        await role.delete(); await interaction.response.send_message("🗑️ Rôle supprimé.")
    @app_commands.command(name="serverlockdown",description="Verrouiller tous les salons textuels.")
    @app_commands.checks.has_permissions(administrator=True)
    async def serverlockdown(self,interaction):
        await interaction.response.defer()
        for ch in interaction.guild.text_channels:
            try:
                ow=ch.overwrites_for(interaction.guild.default_role); ow.send_messages=False
                await ch.set_permissions(interaction.guild.default_role,overwrite=ow)
            except: pass
        await interaction.followup.send("🚨 Lockdown activé.")
    @app_commands.command(name="serverunlock",description="Déverrouiller tous les salons.")
    @app_commands.checks.has_permissions(administrator=True)
    async def serverunlock(self,interaction):
        await interaction.response.defer()
        for ch in interaction.guild.text_channels:
            try:
                ow=ch.overwrites_for(interaction.guild.default_role); ow.send_messages=None
                await ch.set_permissions(interaction.guild.default_role,overwrite=ow)
            except: pass
        await interaction.followup.send("🟢 Lockdown retiré.")
    @app_commands.command(name="modlogs",description="Afficher le salon de logs.")
    async def modlogs(self,interaction):
        s=await self.bot.db.get_settings(interaction.guild.id)
        ch=interaction.guild.get_channel(s["modlog_channel"]) if s and s["modlog_channel"] else None
        await interaction.response.send_message(f"📋 Logs : {ch.mention if ch else 'non configurés'}")
    @app_commands.command(name="setmodlog",description="Définir le salon de logs.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setmodlog(self,interaction,channel:discord.TextChannel):
        await self.bot.db.set_setting(interaction.guild.id,"modlog_channel",channel.id)
        await interaction.response.send_message(f"📋 Logs définis sur {channel.mention}.")
    @app_commands.command(name="automod",description="Afficher l'état de l'AutoMod intégré.")
    async def automod(self,interaction):
        await interaction.response.send_message("🛡️ AutoMod intégré : filtrage des invitations/liens et anti-spam léger.")
    @app_commands.command(name="cleanup",description="Supprimer les messages récents d'un bot.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def cleanup(self,interaction,amount:app_commands.Range[int,1,100]):
        await interaction.response.defer(ephemeral=True)
        msgs=[m async for m in interaction.channel.history(limit=amount) if m.author.bot]
        if msgs: await interaction.channel.delete_messages(msgs)
        await interaction.followup.send(f"🧹 {len(msgs)} messages de bots supprimés.",ephemeral=True)
    @app_commands.command(name="channelinfo",description="Informations sur le salon.")
    async def channelinfo(self,interaction):
        c=interaction.channel
        await interaction.response.send_message(f"📺 **{c.name}**\nID : `{c.id}`\nCatégorie : `{c.category.name if c.category else 'Aucune'}`")
    @commands.Cog.listener()
    async def on_message(self,message):
        if message.author.bot or not message.guild: return
        # anti-spam simple : suppression des invitations
        if "discord.gg/" in message.content.lower() and not message.author.guild_permissions.manage_messages:
            try: await message.delete()
            except: pass

async def setup(bot): await bot.add_cog(Moderation(bot))
