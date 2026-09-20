import asyncio
import discord
from discord.ext import commands
from config import CURRENCY_EMOJI, CURRENCY_NAME


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, name="☕ Membre")
        if role and member.guild.me.guild_permissions.manage_roles and role < member.guild.me.top_role:
            try:
                await member.add_roles(role, reason="Rôle membre automatique")
            except discord.HTTPException:
                pass

        settings = await self.bot.db.get_settings(member.guild.id)
        if settings and settings["welcome_channel"]:
            ch = member.guild.get_channel(settings["welcome_channel"])
            if ch:
                await ch.send(f"☕ Bienvenue {member.mention} dans **{member.guild.name}** !")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        settings = await self.bot.db.get_settings(member.guild.id)
        if settings and settings["leave_channel"]:
            ch = member.guild.get_channel(settings["leave_channel"])
            if ch:
                await ch.send(f"👋 **{member}** vient de quitter le Café Virtuel.")

    async def _create_text(self, guild, name, category, *, overwrites=None, topic=None, slowmode_delay=0):
        kwargs = {
            "category": category,
            "topic": topic,
            "slowmode_delay": slowmode_delay,
            "reason": "Création de la structure du Café Virtuel",
        }
        # discord.py exige un dict uniquement lorsqu'un overwrite est fourni.
        if isinstance(overwrites, dict):
            kwargs["overwrites"] = overwrites
        return await guild.create_text_channel(name, **kwargs)

    async def _create_voice(self, guild, name, category, *, overwrites=None, user_limit=0):
        kwargs = {
            "category": category,
            "user_limit": user_limit,
            "reason": "Création de la structure du Café Virtuel",
        }
        if isinstance(overwrites, dict):
            kwargs["overwrites"] = overwrites
        return await guild.create_voice_channel(name, **kwargs)

    async def _send_embed(self, channel, *, title, description, color=discord.Color.blurple()):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Le Café Virtuel • Ordinateur")
        return await channel.send(embed=embed)

    async def _delete_existing_channels(self, guild, keep_channel):
        # On conserve uniquement le salon où la commande a été lancée jusqu'à la fin,
        # afin de pouvoir afficher la progression. Il sera supprimé en dernier.
        for channel in list(guild.channels):
            if channel.id == keep_channel.id or isinstance(channel, discord.CategoryChannel):
                continue
            try:
                await channel.delete(reason="Réinitialisation complète via &537UP")
                await asyncio.sleep(0.15)
            except (discord.Forbidden, discord.HTTPException):
                pass

        for category in list(guild.categories):
            try:
                await category.delete(reason="Réinitialisation complète via &537UP")
                await asyncio.sleep(0.15)
            except (discord.Forbidden, discord.HTTPException):
                pass

    async def _delete_existing_roles(self, guild):
        me = guild.me
        for role in reversed(guild.roles[1:]):
            if role.managed or role >= me.top_role:
                continue
            try:
                await role.delete(reason="Réinitialisation complète via &537UP")
                await asyncio.sleep(0.12)
            except (discord.Forbidden, discord.HTTPException):
                pass

    async def _create_roles(self, guild):
        # Création du bas vers le haut : Discord place les nouveaux rôles
        # juste au-dessus de @everyone. Le dernier créé sera donc le plus haut.
        role_specs = [
            ("☕ Membre", discord.Permissions.none(), discord.Color.light_grey()),
            ("💎 Booster", discord.Permissions.none(), discord.Color.magenta()),
            ("🤝 Partenaire", discord.Permissions.none(), discord.Color.green()),
            ("🎨 Créateur", discord.Permissions.none(), discord.Color.purple()),
            ("💻 Développeur", discord.Permissions.none(), discord.Color.dark_teal()),
            ("☕ Barista", discord.Permissions(manage_messages=True), discord.Color.gold()),
            ("🎪 Event Manager", discord.Permissions(manage_messages=True, manage_threads=True), discord.Color.orange()),
            ("🎫 Support", discord.Permissions(manage_messages=True, moderate_members=True), discord.Color.blue()),
            ("🛡️ Modérateur Chat", discord.Permissions(manage_messages=True, manage_threads=True, moderate_members=True), discord.Color.orange()),
            ("🛡️ Modérateur", discord.Permissions(
                view_audit_log=True, manage_messages=True, manage_threads=True, kick_members=True,
                ban_members=True, moderate_members=True, manage_nicknames=True, move_members=True,
                mute_members=True, deafen_members=True
            ), discord.Color.orange()),
            ("📣 Community Manager", discord.Permissions(manage_messages=True, manage_threads=True), discord.Color.teal()),
            ("⚙️ Responsable", discord.Permissions(manage_messages=True, manage_channels=True, manage_roles=True), discord.Color.dark_gold()),
            ("👑 Administrateur", discord.Permissions(administrator=True), discord.Color.red()),
            ("👑 Co-Fondateur", discord.Permissions(administrator=True), discord.Color.dark_red()),
            ("👑 Fondateur", discord.Permissions(administrator=True), discord.Color.from_rgb(255, 180, 0)),
        ]
        created = {}
        for name, permissions, color in role_specs:
            role = await guild.create_role(
                name=name, permissions=permissions, color=color, mentionable=False,
                reason="Création des rôles du Café Virtuel",
            )
            created[name] = role
            await asyncio.sleep(0.15)
        return created

    @commands.command(name="537UP")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(
        manage_channels=True,
        manage_roles=True,
        send_messages=True,
        embed_links=True,
        view_channel=True,
    )
    async def setup_command(self, ctx):
        """Réinitialise et construit entièrement Le Café Virtuel."""
        guild = ctx.guild
        old_channel = ctx.channel
        status = await ctx.send(
            "☕ **Reconstruction complète du Café Virtuel...**\n"
            "Les anciens salons et rôles supprimables vont être remplacés."
        )

        try:
            await self._delete_existing_channels(guild, old_channel)
            await self._delete_existing_roles(guild)

            roles = await self._create_roles(guild)
            founder_role = roles["👑 Fondateur"]
            cofounder_role = roles["👑 Co-Fondateur"]
            admin_role = roles["👑 Administrateur"]
            manager_role = roles["⚙️ Responsable"]
            community_role = roles["📣 Community Manager"]
            mod_role = roles["🛡️ Modérateur"]
            chatmod_role = roles["🛡️ Modérateur Chat"]
            support_role = roles["🎫 Support"]
            event_role = roles["🎪 Event Manager"]
            barista_role = roles["☕ Barista"]

            # Rend immédiatement les droits au membre ayant lancé la reconstruction.
            if founder_role < guild.me.top_role:
                try:
                    await ctx.author.add_roles(founder_role, reason="Fondateur ayant lancé &537UP")
                except discord.HTTPException:
                    pass

            everyone = guild.default_role
            bot_member = guild.me

            staff_overwrites = {
                everyone: discord.PermissionOverwrite(view_channel=False),
                founder_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                cofounder_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                manager_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                community_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                mod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                chatmod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                support_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                event_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True),
            }
            readonly_overwrites = {
                everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True),
                founder_role: discord.PermissionOverwrite(send_messages=True),
                cofounder_role: discord.PermissionOverwrite(send_messages=True),
                admin_role: discord.PermissionOverwrite(send_messages=True),
                manager_role: discord.PermissionOverwrite(send_messages=True),
                community_role: discord.PermissionOverwrite(send_messages=True),
                mod_role: discord.PermissionOverwrite(send_messages=True),
                chatmod_role: discord.PermissionOverwrite(send_messages=True),
                support_role: discord.PermissionOverwrite(send_messages=True),
                event_role: discord.PermissionOverwrite(send_messages=True),
                bot_member: discord.PermissionOverwrite(send_messages=True),
            }
            ticket_panel_overwrites = {
                everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True),
                admin_role: discord.PermissionOverwrite(send_messages=True),
                mod_role: discord.PermissionOverwrite(send_messages=True),
                support_role: discord.PermissionOverwrite(send_messages=True),
                bot_member: discord.PermissionOverwrite(send_messages=True),
            }

            info_cat = await guild.create_category("📌 INFORMATIONS", reason="Structure communautaire")
            community_cat = await guild.create_category("💬 COMMUNAUTÉ", reason="Structure communautaire")
            media_cat = await guild.create_category("🎨 CRÉATIONS & MÉDIAS", reason="Structure communautaire")
            cafe_cat = await guild.create_category("☕ LE CAFÉ", reason="Structure communautaire")
            event_cat = await guild.create_category("🎉 ÉVÉNEMENTS", reason="Structure communautaire")
            vocal_cat = await guild.create_category("🔊 VOCAUX", reason="Structure communautaire")
            support_cat = await guild.create_category("🎫 SUPPORT", reason="Structure communautaire")
            staff_cat = await guild.create_category("🛡️ STAFF", overwrites=staff_overwrites, reason="Structure communautaire")
            admin_cat = await guild.create_category("⚙️ ADMINISTRATION", overwrites=staff_overwrites, reason="Structure communautaire")

            welcome = await self._create_text(guild, "👋・bienvenue", info_cat, overwrites=readonly_overwrites)
            rules = await self._create_text(guild, "📜・reglement", info_cat, overwrites=readonly_overwrites)
            infos = await self._create_text(guild, "📌・informations", info_cat, overwrites=readonly_overwrites)
            announcements = await self._create_text(guild, "📢・annonces", info_cat, overwrites=readonly_overwrites)
            faq = await self._create_text(guild, "❓・faq", info_cat, overwrites=readonly_overwrites)
            roles_info = await self._create_text(guild, "🎭・roles", info_cat, overwrites=readonly_overwrites)

            general = await self._create_text(guild, "💬・general", community_cat, topic="Le salon principal du Café Virtuel")
            discussions = await self._create_text(guild, "🗨️・discussions", community_cat)
            questions = await self._create_text(guild, "❔・questions", community_cat)
            presentation = await self._create_text(guild, "🙋・presentations", community_cat)
            media = await self._create_text(guild, "📸・medias", media_cat)
            memes = await self._create_text(guild, "😂・memes", media_cat)
            creations = await self._create_text(guild, "🎨・creations", media_cat)
            art = await self._create_text(guild, "🖼️・art", media_cat)
            dev = await self._create_text(guild, "💻・developpement", media_cat)
            suggestions = await self._create_text(guild, "💡・suggestions", community_cat, slowmode_delay=10)
            partners = await self._create_text(guild, "🤝・partenariats", community_cat, overwrites=readonly_overwrites)
            commands_ch = await self._create_text(guild, "🤖・commandes-bot", community_cat)

            counter = await self._create_text(guild, "☕・comptoir", cafe_cat)
            economy = await self._create_text(guild, "🍪・economie", cafe_cat)
            orders = await self._create_text(guild, "🧾・commandes-cafe", cafe_cat)
            menu = await self._create_text(guild, "📋・menu", cafe_cat, overwrites=readonly_overwrites)
            coffee_chat = await self._create_text(guild, "☕・discussion-cafe", cafe_cat)
            games = await self._create_text(guild, "🎮・jeux", cafe_cat)

            event_info = await self._create_text(guild, "📅・evenements", event_cat, overwrites=readonly_overwrites)
            giveaways = await self._create_text(guild, "🎁・giveaways", event_cat)
            event_chat = await self._create_text(guild, "🎪・organisation", event_cat)

            await self._create_voice(guild, "☕ Café général", vocal_cat)
            await self._create_voice(guild, "💬 Discussion", vocal_cat)
            await self._create_voice(guild, "🎮 Gaming", vocal_cat)
            await self._create_voice(guild, "🎵 Musique", vocal_cat)
            await self._create_voice(guild, "🎨 Créatif", vocal_cat)
            await self._create_voice(guild, "😴 Chill", vocal_cat)
            await self._create_voice(guild, "💤 AFK", vocal_cat)

            tickets = await self._create_text(guild, "🎫・ouvrir-un-ticket", support_cat, overwrites=ticket_panel_overwrites)
            help_ch = await self._create_text(guild, "❓・aide", support_cat)
            ticket_archives = await self._create_text(guild, "📁・archives-tickets", support_cat, overwrites=staff_overwrites)

            staff_chat = await self._create_text(guild, "🛡️・staff-chat", staff_cat)
            staff_announcements = await self._create_text(guild, "📢・staff-annonces", staff_cat)
            logs = await self._create_text(guild, "📋・logs", staff_cat)
            reports = await self._create_text(guild, "🚨・signalements", staff_cat)
            moderation = await self._create_text(guild, "🔨・moderation", staff_cat)
            events_staff = await self._create_text(guild, "🎉・gestion-evenements", staff_cat)
            await self._create_voice(guild, "🛡️ Staff vocal", staff_cat, overwrites=staff_overwrites)

            admin_info = await self._create_text(guild, "⚙️・administration", admin_cat)
            server_config = await self._create_text(guild, "🔧・configuration", admin_cat)
            audit = await self._create_text(guild, "📜・audit", admin_cat)
            founders = await self._create_text(guild, "👑・fondateurs", admin_cat)
            roadmap = await self._create_text(guild, "🗺️・roadmap", admin_cat)

            settings = {
                "ticket_category": support_cat.id,
                "rules_channel": rules.id,
                "ticket_panel_channel": tickets.id,
                "partnership_channel": partners.id,
                "announcements_channel": announcements.id,
                "giveaway_channel": giveaways.id,
                "modlog_channel": logs.id,
                "welcome_channel": welcome.id,
                "leave_channel": general.id,
            }
            for field, value in settings.items():
                await self.bot.db.set_setting(guild.id, field, value)

            await self._send_embed(
                welcome,
                title="☕ Bienvenue au Café Virtuel !",
                description=(
                    "Bienvenue dans notre communauté !\n\n"
                    "📜 Commence par lire le règlement.\n"
                    "💬 Rejoins la discussion dans **#💬・general**.\n"
                    f"🍪 Gagne des {CURRENCY_NAME} avec `/work` et `/daily`.\n"
                    "🎫 Besoin d'aide ? Ouvre un ticket.\n\n"
                    "Passe un bon moment parmi nous ☕"
                ),
                color=discord.Color.orange(),
            )

            await self._send_embed(
                rules,
                title="📜 Règlement du Café Virtuel",
                description=(
                    "**1. Respect** — Respecte tous les membres, sans insultes ni harcèlement.\n\n"
                    "**2. Spam et flood** — Évite les messages répétitifs, mentions abusives et spam.\n\n"
                    "**3. Contenu** — Pas de contenu choquant, illégal ou inadapté au serveur.\n\n"
                    "**4. Publicité** — La publicité sauvage et les invitations non autorisées sont interdites.\n\n"
                    "**5. Salons** — Utilise les salons selon leur thème pour garder le serveur lisible.\n\n"
                    "**6. Vie privée** — Ne partage pas d'informations personnelles sur quelqu'un sans son accord.\n\n"
                    "**7. Modération** — Les consignes du staff doivent être respectées.\n\n"
                    "**8. Discord** — Les Conditions d'utilisation et règles de Discord restent applicables."
                ),
            )

            await self._send_embed(
                infos,
                title="📌 Le Café Virtuel",
                description=(
                    "Le Café Virtuel est un espace communautaire pour discuter, partager, créer et se détendre.\n\n"
                    "☕ **Le Café** — économie, commandes et activités\n"
                    "💬 **Communauté** — discussions, médias, memes et créations\n"
                    "🔊 **Vocaux** — discussion, gaming et chill\n"
                    "🎫 **Support** — aide et tickets\n"
                    "🤖 **Ordinateur** — utilise `/help` pour voir toutes les commandes"
                ),
            )

            await self._send_embed(
                economy,
                title=f"🍪 Économie — {CURRENCY_NAME}",
                description=(
                    f"{CURRENCY_EMOJI} `/balance` — consulter ton solde\n"
                    "💼 `/work` — travailler au café\n"
                    "🎁 `/daily` — récupérer ta récompense quotidienne\n"
                    "⏱️ `/timer` — voir tes cooldowns\n"
                    "🛒 `/shop` — ouvrir la boutique\n"
                    "☕ `/coffee` — commander un café\n"
                    "🎁 `/freecoffee` — obtenir ton café gratuit quotidien"
                ),
                color=discord.Color.gold(),
            )

            await self._send_embed(
                partners,
                title="🤝 Partenariats",
                description=(
                    "Tu souhaites proposer un partenariat avec **Le Café Virtuel** ?\n\n"
                    "Ouvre un ticket dans le salon prévu et présente ton serveur, ton projet et ce que tu proposes."
                ),
                color=discord.Color.green(),
            )

            await self._send_embed(
                announcements,
                title="📢 Annonces officielles",
                description="Les nouveautés, événements et informations importantes du Café Virtuel seront publiés ici.",
            )
            await self._send_embed(
                giveaways,
                title="🎉 Giveaways",
                description="Les concours et giveaways du serveur apparaîtront dans ce salon.",
                color=discord.Color.gold(),
            )
            await self._send_embed(
                suggestions,
                title="💡 Suggestions",
                description="Partage tes idées avec `/suggest` pour aider à améliorer Le Café Virtuel.",
                color=discord.Color.green(),
            )
            await self._send_embed(
                counter,
                title="☕ Le comptoir",
                description="Bienvenue au comptoir ! Discute autour d'un café virtuel et utilise les commandes café d'Ordinateur.",
                color=discord.Color.orange(),
            )

            await self._send_embed(
                faq, title="❓ FAQ",
                description="Les réponses aux questions fréquentes du serveur seront regroupées ici. Pour une demande personnelle, utilise le support.",
            )
            await self._send_embed(
                roles_info, title="🎭 Rôles",
                description=(
                    "👑 **Fondateur / Co-Fondateur / Administrateur** — direction du serveur\n"
                    "⚙️ **Responsable** — gestion interne\n"
                    "📣 **Community Manager** — animation de la communauté\n"
                    "🛡️ **Modérateur / Modérateur Chat** — modération\n"
                    "🎪 **Event Manager** — événements\n"
                    "🎫 **Support** — assistance\n"
                    "☕ **Barista** — animation du Café\n"
                    "💻 **Développeur** — projets techniques\n"
                    "🎨 **Créateur** — créations\n"
                    "🤝 **Partenaire** — partenaires\n"
                    "💎 **Booster** — boosters\n"
                    "☕ **Membre** — rôle communautaire"
                ),
            )
            await self._send_embed(
                event_info, title="📅 Événements",
                description="Tous les événements du Café Virtuel seront annoncés ici. 🎉",
                color=discord.Color.gold(),
            )
            await self._send_embed(
                admin_info, title="⚙️ Administration",
                description="Espace réservé à la gestion du serveur et à l'utilisation des outils d'administration d'Ordinateur.",
            )

            ticket_cog = self.bot.get_cog("Tickets")
            if ticket_cog:
                await ticket_cog.post_panel(tickets)

            await general.send(
                "✅ **Le Café Virtuel est prêt !** ☕\n"
                "La structure communautaire, les rôles, les salons, les vocaux et les panneaux ont été créés."
            )

            # L'ancien salon ayant servi au lancement n'appartient plus à la nouvelle structure.
            try:
                await old_channel.delete(reason="Fin de la reconstruction via &537UP")
            except (discord.Forbidden, discord.HTTPException):
                try:
                    await status.edit(content=f"✅ Reconstruction terminée. Salon principal : {general.mention}")
                except discord.HTTPException:
                    pass

        except discord.Forbidden:
            try:
                await status.edit(
                    content=(
                        "❌ Permissions insuffisantes. Ordinateur doit avoir **Gérer les salons**, "
                        "**Gérer les rôles**, **Envoyer des messages** et **Intégrer des liens**, "
                        "et son rôle doit être placé assez haut dans la hiérarchie."
                    )
                )
            except discord.HTTPException:
                pass
        except discord.HTTPException as exc:
            try:
                await status.edit(content=f"❌ Discord a refusé une étape : `{exc}`")
            except discord.HTTPException:
                pass

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send(f"🏓 Pong ! `{round(self.bot.latency * 1000)}ms`")

    @commands.command(name="commands")
    async def commands_prefix(self, ctx):
        await ctx.send("Les commandes principales sont disponibles avec `/help`. Reconstruction administrateur : `&537UP`.")


async def setup(bot):
    await bot.add_cog(Core(bot))
