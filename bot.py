import discord
from discord.ext import commands, tasks
import asyncio
import time
import random
from database.database import Database
from config import TOKEN, PREFIX, BOT_NAME, MESSAGE_XP_MIN, MESSAGE_XP_MAX

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True
INTENTS.guilds = True

class Ordinateur(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=INTENTS,
            help_command=None,
            case_insensitive=True
        )
        self.db = Database()
        self.giveaway_task = None

    async def setup_hook(self):
        await self.db.init()
        extensions = [
            "cogs.core", "cogs.economy", "cogs.levels", "cogs.moderation",
            "cogs.cafe", "cogs.tickets", "cogs.server", "cogs.giveaways"
        ]
        for ext in extensions:
            await self.load_extension(ext)
        await self.tree.sync()
        self.giveaway_task = asyncio.create_task(self.giveaway_loop())

    async def on_ready(self):
        print(f"Connecté : {self.user} ({self.user.id})")
        print(f"Serveurs : {len(self.guilds)}")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="Le Café Virtuel ☕")
        )

    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        old_level, new_level = await self.db.add_xp(
            message.guild.id, message.author.id, random.randint(MESSAGE_XP_MIN, MESSAGE_XP_MAX)
        )
        if new_level > old_level and new_level > 0:
            try:
                await message.channel.send(f"🎉 {message.author.mention} passe niveau **{new_level}** !")
            except discord.HTTPException:
                pass
        await self.process_commands(message)

    async def giveaway_loop(self):
        await self.wait_until_ready()
        while not self.is_closed():
            rows = await self.db.active_giveaways()
            now = int(time.time())
            for row in rows:
                if row["end_at"] <= now:
                    cog = self.get_cog("Giveaways")
                    if cog:
                        await cog.finish_giveaway(row["message_id"])
            await asyncio.sleep(10)

bot = Ordinateur()

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN manquant dans le fichier .env")

bot.run(TOKEN)
