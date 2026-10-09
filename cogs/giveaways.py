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
        try:
            msg = interaction.message
            if msg is None:
                return await interaction.response.send_message(
                    "❌ Message du giveaway introuvable.", ephemeral=True
                )

            # Add the reaction only if the member has not already entered.
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            already_entered = False
            if reaction:
                already_entered = any(
                    user.id == interaction.user.id
                    async for user in reaction.users()
                )

            if not already_entered:
                await msg.add_reaction("🎉")

            # Re-read reactions so the displayed count reflects the actual entries.
            msg = await msg.channel.fetch_message(msg.id)
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            count = 0
            if reaction:
                count = sum(
                    1 async for user in reaction.users() if not user.bot
                )

            embed = msg.embeds[0].copy() if msg.embeds else discord.Embed(title="🎉 GIVEAWAY")
            embed.set_field_at(
                0,
                name="👥 Participants",
                value=f"**{count}**",
                inline=True,
            ) if embed.fields and embed.fields[0].name == "👥 Participants" else embed.add_field(
                name="👥 Participants", value=f"**{count}**", inline=True
            )
            await msg.edit(embed=embed)

            response = "🎉 Ta participation est enregistrée !" if not already_entered else "✅ Tu participes déjà à ce giveaway."
            await interaction.response.send_message(response, ephemeral=True)
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Impossible de mettre à jour le giveaway. Vérifie les permissions du bot.",
                    ephemeral=True,
                )

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def finish_giveaway(self, message_id):
        rows = await self.bot.db.active_giveaways()
        row = next((r for r in rows if r["message_id"] == message_id), None)
        if not row:
            return

        ch = self.bot.get_channel(row["channel_id"])
        if not ch:
            await self.bot.db.end_giveaway(message_id)
            return

        try:
            msg = await ch.fetch_message(message_id)
        except discord.HTTPException:
            await self.bot.db.end_giveaway(message_id)
            return

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        users = [u async for u in reaction.users() if not u.bot] if reaction else []
        count = len(users)

        if not users:
            text = "😢 Aucun participant."
        else:
            winners = random.sample(users, min(row["winners"], len(users)))
            text = "🎉 Gagnants : " + ", ".join(u.mention for u in winners) + f"\n🎁 Prix : **{row['prize']}**"

        embed = discord.Embed(
            title="🎉 GIVEAWAY TERMINÉ",
            description=text,
            color=discord.Color.dark_gold(),
        )
        embed.add_field(name="👥 Participants", value=f"**{count}**", inline=True)
        await msg.edit(embed=embed, view=None)
        await ch.send(text)
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
        m = re.fullmatch(r"\s*(\d+)\s*([smhd])\s*", duration.lower())
        if not m:
            return await interaction.response.send_message(
                "❌ Durée invalide. Ex: `10m`, `2h`, `1d`.", ephemeral=True
            )

        n = int(m.group(1))
        unit = m.group(2)
        seconds = n * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
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
                "Clique sur **Participer** ou réagis avec 🎉 !"
            ),
            color=discord.Color.gold(),
        )
        embed.add_field(name="👥 Participants", value="**0**", inline=True)
        embed.set_footer(text=f"Créé par {interaction.user.display_name}")

        await interaction.response.defer()
        msg = await interaction.channel.send(embed=embed, view=GiveawayButton(self, 0))
        await msg.add_reaction("🎉")
        await self.bot.db.save_giveaway(
            (msg.id, interaction.guild.id, interaction.channel.id, prize, winners, end, 0)
        )
        await interaction.followup.send("🎉 Giveaway créé.", ephemeral=True)

    @app_commands.command(name="giveawayend", description="Terminer immédiatement un giveaway.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveawayend(self, interaction: discord.Interaction, message_id: str):
        try:
            mid = int(message_id)
        except ValueError:
            return await interaction.response.send_message("❌ ID invalide.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        await self.finish_giveaway(mid)
        await interaction.followup.send("🎉 Giveaway terminé.", ephemeral=True)

    @app_commands.command(name="reroll", description="Reroll un giveaway terminé.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            mid = int(message_id)
            msg = await interaction.channel.fetch_message(mid)
        except (ValueError, discord.HTTPException):
            return await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        users = [u async for u in reaction.users() if not u.bot] if reaction else []
        if not users:
            return await interaction.response.send_message("❌ Aucun participant.", ephemeral=True)

        winner = random.choice(users)
        await interaction.response.send_message(f"🔄 Nouveau gagnant : {winner.mention} 🎉")

async def setup(bot):
    await bot.add_cog(Giveaways(bot))
