import discord
from discord import app_commands
from discord.ext import commands
import random, time
from config import CURRENCY_EMOJI, CURRENCY_NAME, DAILY_REWARD, WORK_COOLDOWN, FREE_COFFEE_COOLDOWN
from utils import fmt_time, cooldown_text, money, item_price, item_display

class InventorySelect(discord.ui.Select):
    def __init__(self, cog, items):
        self.cog = cog
        options = []
        for row in items:
            display = item_display(row["item"])
            options.append(discord.SelectOption(
                label=display[:100],
                value=row["item"],
                description=f"Quantité : {row['amount']}"[:100],
                emoji=display[0]
            ))
        super().__init__(placeholder="Choisis un objet à utiliser…", options=options)

    async def callback(self, interaction):
        await self.cog.use_item(interaction, self.values[0])


class InventoryView(discord.ui.View):
    def __init__(self, cog, items):
        super().__init__(timeout=60)
        self.add_item(InventorySelect(cog, items))


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def base(self, interaction):
        if not interaction.guild:
            await interaction.response.send_message("Commande utilisable sur un serveur.", ephemeral=True)
            return False
        await self.bot.db.ensure_user(interaction.guild.id, interaction.user.id)
        return True

    @app_commands.command(name="balance", description="Voir son solde de Cookies.")
    async def balance(self, interaction):
        if not await self.base(interaction): return
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        await interaction.response.send_message(
            f"🍪 **{interaction.user.display_name}**\n"
            f"Portefeuille : **{money(u['cookies'])}** {CURRENCY_EMOJI}\n"
            f"Banque : **{money(u['bank'])}** 🏦\n"
            f"Total : **{money(u['cookies']+u['bank'])}** {CURRENCY_EMOJI}"
        )

    @app_commands.command(name="daily", description="Récupérer sa récompense quotidienne.")
    async def daily(self, interaction):
        if not await self.base(interaction): return
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        left = cooldown_text(u["last_daily"], 86400)
        if left:
            return await interaction.response.send_message(f"⏳ Reviens dans **{left}**.", ephemeral=True)
        amount = DAILY_REWARD + random.randint(0,100)
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, amount)
        await self.bot.db.set_timestamp(interaction.guild.id, interaction.user.id, "last_daily", int(time.time()))
        await interaction.response.send_message(f"🎁 Daily : **+{amount}** 🍪 !")

    @app_commands.command(name="work", description="Travailler au Café Virtuel.")
    async def work(self, interaction):
        if not await self.base(interaction): return
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        left = cooldown_text(u["last_work"], WORK_COOLDOWN)
        if left:
            return await interaction.response.send_message(f"☕ Tu es encore en pause. `/timer` → **{left}**.", ephemeral=True)
        jobs = [
            ("barista", 60, 180, "☕ Tu as préparé des cafés pour les clients !"),
            ("serveur", 50, 160, "🍰 Tu as servi les clients !"),
            ("cuisinier", 80, 220, "👨‍🍳 Tu as préparé une fournée !"),
            ("caissier", 55, 190, "💳 Tu as tenu la caisse !")
        ]
        job, lo, hi, text = random.choice(jobs)
        amount = random.randint(lo,hi)
        total = amount + u["level"] * 2
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, total)
        await self.bot.db.set_timestamp(interaction.guild.id, interaction.user.id, "last_work", int(time.time()))
        await interaction.response.send_message(f"{text}\n💼 Métier : **{job}**\n💰 Gain : **+{total}** 🍪")

    @app_commands.command(name="timer", description="Voir les cooldowns de tes commandes.")
    async def timer(self, interaction):
        if not await self.base(interaction): return
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        now = time.time()
        def stat(last, cd):
            return "🟢 Disponible" if now-last >= cd else f"⏳ {fmt_time(cd-(now-last))}"
        await interaction.response.send_message(
            f"⏱️ **Tes timers**\n💼 Work : {stat(u['last_work'], WORK_COOLDOWN)}\n"
            f"🎁 Daily : {stat(u['last_daily'], 86400)}\n☕ Café offert : {stat(u['last_freecoffee'], FREE_COFFEE_COOLDOWN)}\n"
            f"🎲 Crime : {stat(u['last_crime'], 3600)}\n🥷 Rob : {stat(u['last_rob'], 7200)}"
        )

    @app_commands.command(name="freecoffee", description="Recevoir un café gratuit chaque jour.")
    async def freecoffee(self, interaction):
        if not await self.base(interaction): return
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        left = cooldown_text(u["last_freecoffee"], FREE_COFFEE_COOLDOWN)
        if left:
            return await interaction.response.send_message(f"☕ Ton café gratuit revient dans **{left}**.", ephemeral=True)
        await self.bot.db.add_item(interaction.guild.id, interaction.user.id, "cafe")
        await self.bot.db.set_timestamp(interaction.guild.id, interaction.user.id, "last_freecoffee", int(time.time()))
        await interaction.response.send_message("☕ **Café offert !** Il a été ajouté à ton inventaire.")

    @app_commands.command(name="shop", description="Voir la boutique.")
    async def shop(self, interaction):
        desc = "\n".join([
            "☕ `cafe` — 50 🍪", "🥐 `croissant` — 75 🍪", "🍰 `gateau` — 120 🍪",
            "🍩 `donut` — 100 🍪", "🧋 `bubbletea` — 150 🍪", "🎁 `mysterybox` — 1 000 🍪",
            "💳 `vipcard` — 5 000 🍪"
        ])
        await interaction.response.send_message(embed=discord.Embed(title="🛒 Boutique du Café", description=desc, color=discord.Color.gold()))

    @app_commands.command(name="buy", description="Acheter un objet dans la boutique.")
    async def buy(self, interaction, item: str, amount: app_commands.Range[int,1,50]=1):
        if not await self.base(interaction): return
        price = item_price(item)
        if price is None:
            return await interaction.response.send_message("❌ Objet inconnu. Fais `/shop`.", ephemeral=True)
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        total = price * amount
        if u["cookies"] < total:
            return await interaction.response.send_message(f"❌ Il te manque **{total-u['cookies']}** 🍪.", ephemeral=True)
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, -total)
        await self.bot.db.add_item(interaction.guild.id, interaction.user.id, item.lower(), amount)
        await interaction.response.send_message(f"🛍️ Achat : **{amount}× {item_display(item)}** pour **{total}** 🍪.")

    @app_commands.command(name="inventory", description="Voir son inventaire.")
    async def inventory(self, interaction):
        if not await self.base(interaction): return
        rows = await self.bot.db.get_inventory(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("🎒 Ton inventaire est vide.")
        desc = "\n".join(f"{item_display(r['item'])} × **{r['amount']}**" for r in rows)
        await interaction.response.send_message(embed=discord.Embed(title="🎒 Inventaire", description=desc))

    async def use_item(self, interaction, item):
        if not await self.base(interaction): return
        item = item.lower()
        if not await self.bot.db.remove_item(interaction.guild.id, interaction.user.id, item):
            return await interaction.response.send_message("❌ Tu n'as plus cet objet dans ton inventaire.", ephemeral=True)
        rewards = {
            "cafe": (20, 50, "☕ Café consommé !"), "croissant": (30, 70, "🥐 Croissant dégusté !"),
            "gateau": (50, 110, "🍰 Gâteau dégusté !"), "donut": (35, 80, "🍩 Donut mangé !"),
            "bubbletea": (60, 130, "🧋 Bubble Tea dégusté !")
        }
        if item == "mysterybox":
            gain = random.randint(100, 1800)
            await self.bot.db.change_money(interaction.guild.id, interaction.user.id, gain)
            return await interaction.response.send_message(f"🎁 Mystery Box ouverte : **+{gain}** 🍪 !")
        if item == "vipcard":
            gain = random.randint(250, 750)
            await self.bot.db.change_money(interaction.guild.id, interaction.user.id, gain)
            return await interaction.response.send_message(f"💳 Carte VIP utilisée ! Bonus : **+{gain}** 🍪.")
        if item not in rewards:
            await self.bot.db.add_item(interaction.guild.id, interaction.user.id, item)
            return await interaction.response.send_message("❌ Cet objet n'est pas utilisable.", ephemeral=True)
        lo, hi, text = rewards[item]
        gain = random.randint(lo,hi)
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, gain)
        await interaction.response.send_message(f"{text}\n✨ Bonus : **+{gain}** 🍪")

    @app_commands.command(name="use", description="Choisir un objet de ton inventaire à utiliser.")
    async def use(self, interaction):
        if not await self.base(interaction): return
        rows = await self.bot.db.get_inventory(interaction.guild.id, interaction.user.id)
        usable = [r for r in rows if r["item"] in {"cafe","croissant","gateau","donut","bubbletea","mysterybox","vipcard"}]
        if not usable:
            return await interaction.response.send_message("🎒 Aucun objet utilisable dans ton inventaire.", ephemeral=True)
        await interaction.response.send_message(
            embed=discord.Embed(title="🎒 Utiliser un objet", description="Sélectionne directement l'objet que tu veux utiliser.", color=discord.Color.blurple()),
            view=InventoryView(self, usable),
            ephemeral=True
        )

    @app_commands.command(name="pay", description="Donner des Cookies à un membre.")
    async def pay(self, interaction, member: discord.Member, amount: app_commands.Range[int,1,1000000]):
        if not await self.base(interaction): return
        if member.bot or member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Cible invalide.", ephemeral=True)
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        if u["cookies"] < amount:
            return await interaction.response.send_message("❌ Solde insuffisant.", ephemeral=True)
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, -amount)
        await self.bot.db.change_money(interaction.guild.id, member.id, amount)
        await interaction.response.send_message(f"💸 {interaction.user.mention} donne **{amount}** 🍪 à {member.mention}.")

    @app_commands.command(name="deposit", description="Déposer des Cookies en banque.")
    async def deposit(self, interaction, amount: app_commands.Range[int,1,1000000]):
        if not await self.base(interaction): return
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        if u["cookies"] < amount:
            return await interaction.response.send_message("❌ Solde insuffisant.", ephemeral=True)
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, -amount)
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, amount, bank=True)
        await interaction.response.send_message(f"🏦 Dépôt de **{amount}** 🍪 effectué.")

    @app_commands.command(name="withdraw", description="Retirer des Cookies de la banque.")
    async def withdraw(self, interaction, amount: app_commands.Range[int,1,1000000]):
        if not await self.base(interaction): return
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        if u["bank"] < amount:
            return await interaction.response.send_message("❌ Solde bancaire insuffisant.", ephemeral=True)
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, -amount, bank=True)
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, amount)
        await interaction.response.send_message(f"💵 Retrait de **{amount}** 🍪 effectué.")

    @app_commands.command(name="leaderboard", description="Classement des plus riches.")
    async def leaderboard(self, interaction):
        if not await self.base(interaction): return
        rows = await self.bot.db.leaderboard(interaction.guild.id)
        desc = "\n".join(f"**{i}.** <@{r['user_id']}> — {money(r['cookies']+r['bank'])} 🍪" for i,r in enumerate(rows,1))
        await interaction.response.send_message(embed=discord.Embed(title="🏆 Richesse", description=desc or "Aucune donnée."))

    @app_commands.command(name="richest", description="Voir les membres les plus riches.")
    async def richest(self, interaction):
        await self.leaderboard.callback(self, interaction)

    @app_commands.command(name="economy", description="Statistiques de l'économie du serveur.")
    async def economy(self, interaction):
        if not await self.base(interaction): return
        rows = await self.bot.db.leaderboard(interaction.guild.id, 100)
        total = sum(r["cookies"]+r["bank"] for r in rows)
        await interaction.response.send_message(f"📊 Économie : **{money(total)}** 🍪 répartis entre les membres enregistrés.")

    @app_commands.command(name="beg", description="Mendier quelques Cookies.")
    async def beg(self, interaction):
        if not await self.base(interaction): return
        gain = random.randint(10,70)
        await self.bot.db.change_money(interaction.guild.id, interaction.user.id, gain)
        await interaction.response.send_message(f"🥺 Un client compatissant te donne **{gain}** 🍪.")

    @app_commands.command(name="crime", description="Tenter un petit crime virtuel.")
    async def crime(self, interaction):
        if not await self.base(interaction): return
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        left = cooldown_text(u["last_crime"],3600)
        if left: return await interaction.response.send_message(f"⏳ Reviens dans **{left}**.", ephemeral=True)
        await self.bot.db.set_timestamp(interaction.guild.id, interaction.user.id, "last_crime", int(time.time()))
        if random.random() < .7:
            gain = random.randint(80,300)
            await self.bot.db.change_money(interaction.guild.id, interaction.user.id, gain)
            await interaction.response.send_message(f"🕵️ Coup réussi : **+{gain}** 🍪.")
        else:
            loss = min(u["cookies"], random.randint(20,100))
            await self.bot.db.change_money(interaction.guild.id, interaction.user.id, -loss)
            await interaction.response.send_message(f"🚨 Tu t'es fait prendre ! **-{loss}** 🍪.")

    @app_commands.command(name="rob", description="Tenter de voler un membre.")
    async def rob(self, interaction, member: discord.Member):
        if not await self.base(interaction): return
        if member.bot or member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Cible invalide.", ephemeral=True)
        u = await self.bot.db.get_user(interaction.guild.id, interaction.user.id)
        left = cooldown_text(u["last_rob"],7200)
        if left: return await interaction.response.send_message(f"⏳ Reviens dans **{left}**.", ephemeral=True)
        await self.bot.db.set_timestamp(interaction.guild.id, interaction.user.id, "last_rob", int(time.time()))
        target = await self.bot.db.get_user(interaction.guild.id, member.id)
        amount = random.randint(20, min(250, max(20,target["cookies"]))) if target["cookies"] else 0
        if amount and random.random() < .45:
            await self.bot.db.change_money(interaction.guild.id, member.id, -amount)
            await self.bot.db.change_money(interaction.guild.id, interaction.user.id, amount)
            await interaction.response.send_message(f"🥷 Vol réussi ! **+{amount}** 🍪.")
        else:
            fine = random.randint(10,60)
            loss = min(u["cookies"], fine)
            await self.bot.db.change_money(interaction.guild.id, interaction.user.id, -loss)
            await interaction.response.send_message(f"🚔 Raté ! Amende : **-{loss}** 🍪.")

async def setup(bot):
    await bot.add_cog(Economy(bot))
