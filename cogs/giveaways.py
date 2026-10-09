import discord, time, random, re
from discord import app_commands
from discord.ext import commands


class GiveawayButton(discord.ui.View):
    def __init__(self, cog, message_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.message_id = message_id

    @discord.ui.button(
        label="Participer",
        emoji="🎉",
        style=discord.ButtonStyle.success,
        custom_id="ordinateur_giveaway_enter",
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        rows = await self.cog.bot.db.active_giveaways()
        giveaway = next((row for row in rows if row["message_id"] == message_id), None)
        if giveaway is None:
            return await interaction.response.send_message(
                "❌ Ce giveaway est terminé ou n'est plus disponible.", ephemeral=True
            )

        added = await self.cog.bot.db.enter_giveaway(message_id, interaction.user.id)
        # Acknowledge the interaction immediately so Discord does not time out
        # while the message is being refreshed.
        await interaction.response.send_message(
            "🎉 Ta participation est enregistrée !" if added else "✅ Tu participes déjà à ce giveaway.",
            ephemeral=True,
        )
        await self.cog.refresh_participant_count(interaction.message)


class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def refresh_participant_count(self, message):
        """Update the visible participant total on the giveaway embed."""
        participants = await self.bot.db.giveaway_entries(message.id)
        embed = message.embeds[0].copy() if message.embeds else discord.Embed(title="🎉 GIVEAWAY")
        count = len(participants)
        field_index = next(
            (i for i, field in enumerate(embed.fields) if field.name == "👥 Participants"),
            None,
        )
        if field_index is None:
            embed.add_field(name="👥 Participants", value=f"**{count}**", inline=True)
        else:
            embed.set_field_at(
                field_index, name="👥 Participants", value=f"**{count}**", inline=True
            )
        try:
            await message.edit(embed=embed)
        except discord.HTTPException:
            pass

    async def finish_giveaway(self, message_id):
        rows = await self.bot.db.active_giveaways()
        row = next((r for r in rows if r["message_id"] == message_id), None)
        if not row:
            return

        channel = self.bot.get_channel(row["channel_id"])
        if not channel:
            await self.bot.db.end_giveaway(message_id)
            return

        try:
            message = await channel.fetch_message(message_id)
        except discord.HTTPException:
            await self.bot.db.end_giveaway(message_id)
            return

        participant_ids = await self.bot.db.giveaway_entries(message_id)
        eligible = []
        for user_id in participant_ids:
            try:
                eligible.append(await self.bot.fetch_user(user_id))
            except discord.HTTPException:
                continue

        count = len(eligible)
        if not eligible:
            text = "😢 Aucun participant."
        else:
            winners = random.sample(eligible, min(row["winners"], count))
            text = "🎉 Gagnants : " + ", ".join(user.mention for user in winners) + f"\n🎁 Prix : **{row['prize']}**"

        embed = discord.Embed(
            title="🎉 GIVEAWAY TERMINÉ",
            description=text,
            color=discord.Color.dark_gold(),
        )
        embed.add_field(name="👥 Participants", value=f"**{count}**", inline=True)
        await message.edit(embed=embed, view=None)
        await channel.send(text)
        await self.bot.db.end_giveaway(message_id)

    @app_commands.command(name="giveaway", description="Créer un giveaway.")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(duration="Durée comme 10m, 2h, 1d", prize="Prix", winners="Nombre de gagnants")
    async def giveaway(
        self,
        interaction: discord.Interaction,
        duration: str,
        prize: str,
        winners: app_commands.Range[int, 1, 20] = 1,
    ):
        match = re.fullmatch(r"\s*(\d+)\s*([smhd])\s*", duration.lower())
        if not match:
            return await interaction.response.send_message(
                "❌ Durée invalide. Ex: `10m`, `2h`, `1d`.", ephemeral=True
            )

        amount = int(match.group(1))
        unit = match.group(2)
        seconds = amount * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        if seconds < 10 or seconds > 604800:
            return await interaction.response.send_message(
                "❌ Durée : 10 secondes à 7 jours.", ephemeral=True
            )

        end = int(time.time() + seconds)
        embed = discord.Embed(
            title="🎉 GIVEAWAY",
            description=(
                f"🎁 Prix : **{prize}**\n"
                f"👑 Gagnants : **{winners}**\n"
                f"⏰ Fin : <t:{end}:R>\n\n"
                "Clique sur **Participer** pour rejoindre le tirage !"
            ),
            color=discord.Color.gold(),
        )
        embed.add_field(name="👥 Participants", value="**0**", inline=True)
        embed.set_footer(text=f"Créé par {interaction.user.display_name}")

        await interaction.response.defer()
        message = await interaction.channel.send(embed=embed, view=GiveawayButton(self, 0))
        await self.bot.db.save_giveaway(
            (message.id, interaction.guild.id, interaction.channel.id, prize, winners, end, 0)
        )
        await interaction.followup.send("🎉 Giveaway créé.", ephemeral=True)

    @app_commands.command(name="giveawayend", description="Terminer immédiatement un giveaway.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveawayend(self, interaction: discord.Interaction, message_id: str):
        try:
            message_id_int = int(message_id)
        except ValueError:
            return await interaction.response.send_message("❌ ID invalide.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        await self.finish_giveaway(message_id_int)
        await interaction.followup.send("🎉 Giveaway terminé.", ephemeral=True)

    @app_commands.command(name="reroll", description="Reroll un giveaway terminé.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            mid = int(message_id)
            message = await interaction.channel.fetch_message(mid)
        except (ValueError, discord.HTTPException):
            return await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)

        # Reroll uses the participants saved for the original giveaway.
        participant_ids = await self.bot.db.giveaway_entries(mid)
        users = []
        for user_id in participant_ids:
            try:
                users.append(await self.bot.fetch_user(user_id))
            except discord.HTTPException:
                continue
        if not users:
            return await interaction.response.send_message("❌ Aucun participant enregistré.", ephemeral=True)

        winner = random.choice(users)
        await interaction.response.send_message(f"🔄 Nouveau gagnant : {winner.mention} 🎉")

async def setup(bot):
    cog = Giveaways(bot)
    await bot.add_cog(cog)
    # Re-register the persistent button view after restarts.
    for row in await bot.db.active_giveaways():
        bot.add_view(GiveawayButton(cog, row["message_id"]), message_id=row["message_id"])
