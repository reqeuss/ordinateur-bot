import discord
from discord import app_commands
from discord.ext import commands
from utils import money

class Levels(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="profile", description="Voir son profil.")
    async def profile(self, interaction, member: discord.Member=None):
        member = member or interaction.user
        u = await self.bot.db.get_user(interaction.guild.id, member.id)
        await interaction.response.send_message(embed=discord.Embed(
            title=f"👤 Profil de {member.display_name}",
            description=f"⭐ Niveau : **{u['level']}**\n✨ XP : **{u['xp']}**\n🍪 Cookies : **{money(u['cookies'])}**\n🏦 Banque : **{money(u['bank'])}**",
            color=discord.Color.blurple()
        ))

    @app_commands.command(name="rank", description="Voir son rang.")
    async def rank(self, interaction):
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        rows = await self.bot.db.top_level(interaction.guild.id, 1000)
        pos = next((i for i,r in enumerate(rows,1) if r["user_id"]==interaction.user.id), None)
        await interaction.response.send_message(f"⭐ Tu es niveau **{u['level']}**, rang **#{pos or '?'}** avec **{u['xp']} XP**.")

    @app_commands.command(name="level", description="Voir le niveau d'un membre.")
    async def level(self, interaction, member: discord.Member=None):
        member = member or interaction.user
        u = await self.bot.db.get_user(interaction.guild.id, member.id)
        await interaction.response.send_message(f"⭐ {member.mention} est niveau **{u['level']}** avec **{u['xp']} XP**.")

    @app_commands.command(name="levelboard", description="Classement des niveaux.")
    async def levelboard(self, interaction):
        rows = await self.bot.db.top_level(interaction.guild.id)
        desc = "\n".join(f"**{i}.** <@{r['user_id']}> — niv. **{r['level']}** ({r['xp']} XP)" for i,r in enumerate(rows,1))
        await interaction.response.send_message(embed=discord.Embed(title="🏆 Classement XP", description=desc or "Aucune donnée."))

    @app_commands.command(name="setlevel", description="Définir le niveau d'un membre.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setlevel(self, interaction, member: discord.Member, level: app_commands.Range[int,0,1000]):
        u = await self.bot.db.get_user(interaction.guild.id, member.id)
        # approximate XP matching the level formula
        xp = level * level * 100
        await self.bot.db.add_xp(interaction.guild.id, member.id, max(0, xp-u["xp"]))
        await interaction.response.send_message(f"⭐ Niveau de {member.mention} défini à **{level}**.")

    @app_commands.command(name="setxp", description="Ajouter de l'XP à un membre.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setxp(self, interaction, member: discord.Member, amount: app_commands.Range[int,0,1000000]):
        await self.bot.db.add_xp(interaction.guild.id, member.id, amount)
        await interaction.response.send_message(f"✨ **{amount} XP** ajoutés à {member.mention}.")

async def setup(bot): await bot.add_cog(Levels(bot))
