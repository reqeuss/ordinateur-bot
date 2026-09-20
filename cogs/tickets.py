import discord, time
from discord import app_commands
from discord.ext import commands

class TicketView(discord.ui.View):
    def __init__(self,cog): super().__init__(timeout=None); self.cog=cog
    @discord.ui.button(label="Créer un ticket",emoji="🎫",style=discord.ButtonStyle.primary,custom_id="ordinateur:create_ticket")
    async def create(self,interaction,button):
        await self.cog.create_ticket(interaction)

class CloseView(discord.ui.View):
    def __init__(self,cog): super().__init__(timeout=None); self.cog=cog
    @discord.ui.button(label="Fermer",emoji="🔒",style=discord.ButtonStyle.danger,custom_id="ordinateur:close_ticket")
    async def close(self,interaction,button):
        await self.cog.close(interaction)

class Tickets(commands.Cog):
    def __init__(self,bot): self.bot=bot

    async def cog_load(self):
        self.bot.add_view(TicketView(self)); self.bot.add_view(CloseView(self))

    async def post_panel(self, channel):
        await channel.send(
            embed=discord.Embed(
                title="🎫 Centre de tickets",
                description=(
                    "Besoin d'aide ? Clique sur **Créer un ticket**.\n\n"
                    "📩 Support\n🤝 Partenariat\n💼 Collaboration\n❓ Question"
                ),
                color=discord.Color.blurple(),
            ),
            view=TicketView(self),
        )

    async def post_panel_if_missing(self, channel):
        """Publie le panneau seulement s'il n'existe pas déjà."""
        try:
            async for message in channel.history(limit=50):
                if message.author.id == self.bot.user.id and message.embeds:
                    if (message.embeds[0].title or "") == "🎫 Centre de tickets":
                        return
        except (discord.Forbidden, discord.HTTPException):
            return
        await self.post_panel(channel)

    async def create_ticket(self,interaction):
        existing=await self.bot.db.ticket_by_owner(interaction.guild.id,interaction.user.id)
        if existing:
            ch=interaction.guild.get_channel(existing["channel_id"])
            if ch:return await interaction.response.send_message(f"🎫 Tu as déjà un ticket : {ch.mention}",ephemeral=True)
        settings=await self.bot.db.get_settings(interaction.guild.id)
        cat=interaction.guild.get_channel(settings["ticket_category"]) if settings and settings["ticket_category"] else None
        if not cat:
            cat=discord.utils.get(interaction.guild.categories,name="🎫 TICKETS")
        overwrites={
            interaction.guild.default_role:discord.PermissionOverwrite(view_channel=False),
            interaction.user:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True),
            interaction.guild.me:discord.PermissionOverwrite(view_channel=True,send_messages=True,manage_channels=True)
        }
        ch=await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}",category=cat,overwrites=overwrites)
        await self.bot.db.save_ticket(ch.id,interaction.guild.id,interaction.user.id,int(time.time()))
        await ch.send(content=interaction.user.mention,embed=discord.Embed(
            title="🎫 Ticket ouvert",
            description="Explique ton besoin ici. Un membre du staff te répondra.\n\n🤝 Pour un partenariat, indique ton serveur/projet et les informations utiles.",
            color=discord.Color.green()),view=CloseView(self))
        await interaction.response.send_message(f"✅ Ticket créé : {ch.mention}",ephemeral=True)

    async def close(self,interaction):
        row=await self.bot.db.ticket_by_owner(interaction.guild.id,interaction.user.id)
        if not row and not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Tu n'es pas propriétaire de ce ticket.",ephemeral=True)
        await interaction.response.send_message("🔒 Fermeture du ticket dans 5 secondes.")
        await self.bot.db.delete_ticket(interaction.channel.id)
        await __import__("asyncio").sleep(5)
        await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")

    @app_commands.command(name="ticket",description="Créer un ticket.")
    async def ticket(self,interaction): await self.create_ticket(interaction)

    @app_commands.command(name="close",description="Fermer le ticket actuel.")
    async def close_cmd(self,interaction): await self.close(interaction)

    @app_commands.command(name="claim",description="Prendre en charge un ticket.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def claim(self,interaction):
        await interaction.response.send_message(f"🛡️ Ticket pris en charge par {interaction.user.mention}.")

    @app_commands.command(name="partnership",description="Créer un ticket de partenariat.")
    async def partnership(self,interaction):
        await self.create_ticket(interaction)
        # The normal ticket flow accepts partnership requests.

    @app_commands.command(name="ticketsetup",description="Reposter le panneau de tickets.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticketsetup(self,interaction):
        await self.post_panel(interaction.channel)
        await interaction.response.send_message("🎫 Panneau envoyé.",ephemeral=True)

async def setup(bot): await bot.add_cog(Tickets(bot))
