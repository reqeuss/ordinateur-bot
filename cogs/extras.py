import random
import discord
from discord import app_commands
from discord.ext import commands


class Extras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="flip", description="Lancer une pièce.")
    async def flip(self, interaction):
        await interaction.response.send_message(
            random.choice(["🪙 **Pile !**", "🪙 **Face !**"])
        )

    @app_commands.command(name="dice", description="Lancer un dé.")
    async def dice(self, interaction, sides: app_commands.Range[int, 2, 100] = 6):
        result = random.randint(1, sides)
        await interaction.response.send_message(
            f"🎲 Tu obtiens **{result}** sur un dé à **{sides}** faces."
        )

    @app_commands.command(name="rps", description="Jouer à pierre-feuille-ciseaux.")
    async def rps(self, interaction, choice: str):
        choices = {"pierre": "🪨", "feuille": "📄", "ciseaux": "✂️"}
        c = choice.lower().strip()

        if c not in choices:
            await interaction.response.send_message(
                "❌ Choisis pierre, feuille ou ciseaux.",
                ephemeral=True,
            )
            return

        bot_choice = random.choice(list(choices))

        if c == bot_choice:
            result = "🤝 Égalité !"
        elif (
            (c == "pierre" and bot_choice == "ciseaux")
            or (c == "feuille" and bot_choice == "pierre")
            or (c == "ciseaux" and bot_choice == "feuille")
        ):
            result = "🎉 Tu gagnes !"
        else:
            result = "😅 Tu perds !"

        await interaction.response.send_message(
            f"🪨📄✂️ Toi : {choices[c]} **{c}**\n"
            f"Ordinateur : {choices[bot_choice]} **{bot_choice}**\n\n"
            f"{result}"
        )

    @app_commands.command(name="random", description="Choisir un nombre aléatoire.")
    async def random_number(self, interaction, minimum: int = 1, maximum: int = 100):
        if minimum > maximum:
            minimum, maximum = maximum, minimum

        result = random.randint(minimum, maximum)
        await interaction.response.send_message(f"🎯 Résultat : **{result}**")

    @app_commands.command(name="8ball", description="Poser une question à la boule magique.")
    async def eightball(self, interaction, question: str):
        answers = [
            "🔮 Oui.",
            "🔮 Non.",
            "🔮 Probablement.",
            "🔮 Pas impossible.",
            "🔮 Demande-moi plus tard.",
            "🔮 Les étoiles sont silencieuses.",
        ]
        await interaction.response.send_message(
            f"🔮 **{question}**\n{random.choice(answers)}"
        )

    @app_commands.command(name="rate", description="Donner une note amusante.")
    async def rate(self, interaction, thing: str):
        score = random.randint(0, 100)
        await interaction.response.send_message(
            f"📊 **{thing}** obtient **{score}%** aujourd’hui."
        )

    @app_commands.command(name="choose", description="Choisir entre plusieurs propositions.")
    async def choose(self, interaction, options: str):
        values = [value.strip() for value in options.split(",") if value.strip()]

        if len(values) < 2:
            await interaction.response.send_message(
                "❌ Donne au moins deux choix séparés par des virgules.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"🎯 Je choisis : **{random.choice(values)}**"
        )

    @app_commands.command(name="cookiegift", description="Offrir quelques Cookies à un membre.")
    async def cookiegift(self, interaction, member: discord.Member):
        if member.bot or member.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Cible invalide.",
                ephemeral=True,
            )
            return

        amount = random.randint(10, 40)
        await self.bot.db.change_money(interaction.guild.id, member.id, amount)

        await interaction.response.send_message(
            f"🎁 {member.mention} reçoit **{amount}** 🍪 "
            f"de la part de {interaction.user.mention} !"
        )


async def setup(bot):
    await bot.add_cog(Extras(bot))
