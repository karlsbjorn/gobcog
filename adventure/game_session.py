import logging
import random
from datetime import datetime
from typing import List, Mapping, MutableMapping, Set, Tuple, Optional

import discord
from redbot.core.commands import Context, commands
from redbot.core.i18n import Translator

from .charsheet import Character, has_funds
from .helpers import escape

# This is split into its own file for future buttons usage
# We will have game sessions inherit discord.ui.View and then we can send a message
# with the buttons required. For now this will sit in its own file.

_ = Translator("Adventure", __file__)
log = logging.getLogger("red.cogs.adventure")


class AttackButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int] = None,
    ):
        super().__init__(label="Attack", style=style, row=row)
        self.style = style
        self.emoji = "\N{DAGGER KNIFE}\N{VARIATION SELECTOR-16}"
        self.action_type = "fight"
        self.label_name = "Attack {}"

    async def send_response(self, interaction: discord.Interaction):
        user = interaction.user
        try:
            c = await Character.from_json(self.view.ctx, self.view.cog.config, user, self.view.cog._daily_bonus)
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            pass
        choices = self.view.cog.ACTION_RESPONSE.get(self.action_type, {})
        heroclass = getattr(c, "heroclass", {"name": "default"})["name"].lower()
        choice = random.choice(choices[heroclass])
        choice = choice.replace("$monster", self.view.challenge)
        left = getattr(c, "left")
        right = getattr(c, "right")
        if left and right:
            weapon = str(left) + str(right)
        if left and not right:
            weapon = str(left)
        if right and not left:
            weapon = str(right)
        if not left and not right:
            weapon = "fists"
        choice = choice.replace("$weapon", weapon)
        god = await self.view.cog.config.god_name()
        if await self.view.cog.config.guild(interaction.guild).god_name():
            god = await self.view.cog.config.guild(interaction.guild).god_name()
        choice = choice.replace("$god", god)
        await interaction.response.send_message(choice, ephemeral=True)

    async def callback(self, interaction: discord.Interaction):
        """Skip to previous track"""
        user = interaction.user
        for x in ["magic", "talk", "pray", "run"]:
            if user in getattr(self.view, x, []):
                getattr(self.view, x).remove(user)
        restricted = self.view.cog.config.restrict()
        if user not in self.view.fight:
            if restricted:
                all_users = []
                for (guild_id, guild_session) in self.view.cog._sessions.items():
                    guild_users_in_game = (
                        guild_session.fight
                        + guild_session.magic
                        + guild_session.talk
                        + guild_session.pray
                        + guild_session.run
                    )
                    all_users = all_users + guild_users_in_game

                if user in all_users:
                    user_id = f"{user.id}-{user.guild.id}"
                    # iterating through reactions here and removing them seems to be expensive
                    # so they can just keep their react on the adventures they can't join
                    if user_id not in self.view.cog._react_messaged:
                        await interaction.response.send_message(
                            _(
                                "**{c}**, you are already in an existing adventure. "
                                "Wait for it to finish before joining another one."
                            ).format(c=escape(user.display_name)),
                            ephemeral=True,
                        )
                        self.view.cog._react_messaged.append(user_id)
                        return
                else:
                    self.view.fight.append(user)
            else:
                self.view.fight.append(user)
            await self.send_response(interaction)
            await self.view.update()
        else:
            await interaction.response.send_message("You are already fighting this monster.", ephemeral=True)


class MagicButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int] = None,
    ):
        super().__init__(label="Magic", style=style, row=row)
        self.style = style
        self.emoji = "\N{SPARKLES}"
        self.action_type = "magic"
        self.label_name = "Magic {}"

    async def send_response(self, interaction: discord.Interaction):
        user = interaction.user
        try:
            c = await Character.from_json(self.view.ctx, self.view.cog.config, user, self.view.cog._daily_bonus)
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            pass
        choices = self.view.cog.ACTION_RESPONSE.get(self.action_type, {})
        heroclass = getattr(c, "heroclass", {"name": "default"})["name"].lower()
        choice = random.choice(choices[heroclass])
        choice = choice.replace("$monster", self.view.challenge)
        left = getattr(c, "left")
        right = getattr(c, "right")
        if left and right:
            weapon = str(left) + str(right)
        if left and not right:
            weapon = str(left)
        if right and not left:
            weapon = str(right)
        if not left and not right:
            weapon = "fists"
        choice = choice.replace("$weapon", weapon)
        god = await self.view.cog.config.god_name()
        if await self.view.cog.config.guild(interaction.guild).god_name():
            god = await self.view.cog.config.guild(interaction.guild).god_name()
        choice = choice.replace("$god", god)
        await interaction.response.send_message(choice, ephemeral=True)

    async def callback(self, interaction: discord.Interaction):
        """Skip to previous track"""
        user = interaction.user
        for x in ["fight", "talk", "pray", "run"]:
            if user in getattr(self.view, x, []):
                getattr(self.view, x).remove(user)
        restricted = self.view.cog.config.restrict()
        if user not in self.view.magic:
            if restricted:
                all_users = []
                for (guild_id, guild_session) in self.view.cog._sessions.items():
                    guild_users_in_game = (
                        guild_session.fight
                        + guild_session.magic
                        + guild_session.talk
                        + guild_session.pray
                        + guild_session.run
                    )
                    all_users = all_users + guild_users_in_game

                if user in all_users:
                    user_id = f"{user.id}-{user.guild.id}"
                    # iterating through reactions here and removing them seems to be expensive
                    # so they can just keep their react on the adventures they can't join
                    if user_id not in self.view.cog._react_messaged:
                        await interaction.response.send_message(
                            _(
                                "**{c}**, you are already in an existing adventure. "
                                "Wait for it to finish before joining another one."
                            ).format(c=escape(user.display_name)),
                            ephemeral=True,
                        )
                        self.view.cog._react_messaged.append(user_id)
                        return
                else:
                    self.view.magic.append(user)
            else:
                self.view.magic.append(user)
            await self.send_response(interaction)
            await self.view.update()
        else:
            await interaction.response.send_message("You have already cast a spell at this monster.", ephemeral=True)


class TalkButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int] = None,
    ):
        super().__init__(label="Talk", style=style, row=row)
        self.style = style
        self.emoji = "\N{LEFT SPEECH BUBBLE}\N{VARIATION SELECTOR-16}"
        self.action_type = "talk"
        self.label_name = "Talk {}"

    async def send_response(self, interaction: discord.Interaction):
        user = interaction.user
        try:
            c = await Character.from_json(self.view.ctx, self.view.cog.config, user, self.view.cog._daily_bonus)
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            pass
        choices = self.view.cog.ACTION_RESPONSE.get(self.action_type, {})
        heroclass = getattr(c, "heroclass", {"name": "default"})["name"].lower()
        choice = random.choice(choices[heroclass])
        choice = choice.replace("$monster", self.view.challenge)
        left = getattr(c, "left")
        right = getattr(c, "right")
        if left and right:
            weapon = str(left) + str(right)
        if left and not right:
            weapon = str(left)
        if right and not left:
            weapon = str(right)
        if not left and not right:
            weapon = "fists"
        choice = choice.replace("$weapon", weapon)
        god = await self.view.cog.config.god_name()
        if await self.view.cog.config.guild(interaction.guild).god_name():
            god = await self.view.cog.config.guild(interaction.guild).god_name()
        choice = choice.replace("$god", god)
        await interaction.response.send_message(choice, ephemeral=True)

    async def callback(self, interaction: discord.Interaction):
        """Skip to previous track"""
        user = interaction.user
        for x in ["fight", "magic", "pray", "run"]:
            if user in getattr(self.view, x, []):
                getattr(self.view, x).remove(user)
        restricted = self.view.cog.config.restrict()
        if user not in self.view.talk:
            if restricted:
                all_users = []
                for (guild_id, guild_session) in self.view.cog._sessions.items():
                    guild_users_in_game = (
                        guild_session.fight
                        + guild_session.magic
                        + guild_session.talk
                        + guild_session.pray
                        + guild_session.run
                    )
                    all_users = all_users + guild_users_in_game

                if user in all_users:
                    user_id = f"{user.id}-{user.guild.id}"
                    # iterating through reactions here and removing them seems to be expensive
                    # so they can just keep their react on the adventures they can't join
                    if user_id not in self.view.cog._react_messaged:
                        await interaction.response.send_message(
                            _(
                                "**{c}**, you are already in an existing adventure. "
                                "Wait for it to finish before joining another one."
                            ).format(c=escape(user.display_name)),
                            ephemeral=True,
                        )
                        self.view.cog._react_messaged.append(user_id)
                        return
                else:
                    self.view.talk.append(user)
            else:
                self.view.talk.append(user)
            await self.send_response(interaction)
            await self.view.update()
        else:
            await interaction.response.send_message("You are already talking to this monster.", ephemeral=True)


class PrayButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int] = None,
    ):
        super().__init__(label="Pray", style=style, row=row)
        self.style = style
        self.emoji = "\N{PERSON WITH FOLDED HANDS}"
        self.action_type = "pray"
        self.label_name = "Pray {}"

    async def send_response(self, interaction: discord.Interaction):
        user = interaction.user
        try:
            c = await Character.from_json(self.view.ctx, self.view.cog.config, user, self.view.cog._daily_bonus)
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            pass
        choices = self.view.cog.ACTION_RESPONSE.get(self.action_type, {})
        heroclass = getattr(c, "heroclass", {"name": "default"})["name"].lower()
        choice = random.choice(choices[heroclass])
        choice = choice.replace("$monster", self.view.challenge)
        left = getattr(c, "left")
        right = getattr(c, "right")
        if left and right:
            weapon = str(left) + str(right)
        if left and not right:
            weapon = str(left)
        if right and not left:
            weapon = str(right)
        if not left and not right:
            weapon = "fists"
        choice = choice.replace("$weapon", weapon)
        god = await self.view.cog.config.god_name()
        if await self.view.cog.config.guild(interaction.guild).god_name():
            god = await self.view.cog.config.guild(interaction.guild).god_name()
        choice = choice.replace("$god", god)
        await interaction.response.send_message(choice, ephemeral=True)

    async def callback(self, interaction: discord.Interaction):
        """Skip to previous track"""
        user = interaction.user
        for x in ["fight", "magic", "talk", "run"]:
            if user in getattr(self.view, x, []):
                getattr(self.view, x).remove(user)
        restricted = self.view.cog.config.restrict()
        if user not in self.view.pray:
            if restricted:
                all_users = []
                for (guild_id, guild_session) in self.view.cog._sessions.items():
                    guild_users_in_game = (
                        guild_session.fight
                        + guild_session.magic
                        + guild_session.talk
                        + guild_session.pray
                        + guild_session.run
                    )
                    all_users = all_users + guild_users_in_game

                if user in all_users:
                    user_id = f"{user.id}-{user.guild.id}"
                    # iterating through reactions here and removing them seems to be expensive
                    # so they can just keep their react on the adventures they can't join
                    if user_id not in self.view.cog._react_messaged:
                        await interaction.response.send_message(
                            _(
                                "**{c}**, you are already in an existing adventure. "
                                "Wait for it to finish before joining another one."
                            ).format(c=escape(user.display_name)),
                            ephemeral=True,
                        )
                        self.view.cog._react_messaged.append(user_id)
                        return
                else:
                    self.view.pray.append(user)
            else:
                self.view.pray.append(user)
            await self.send_response(interaction)
            await self.view.update()
        else:
            await interaction.response.send_message("You are already praying for help against this monster.", ephemeral=True)


class RunButton(discord.ui.Button):
    def __init__(
        self,
        style: discord.ButtonStyle,
        row: Optional[int] = None,
    ):
        super().__init__(label="Run", style=style, row=row)
        self.style = style
        self.emoji = "\N{RUNNER}\N{ZERO WIDTH JOINER}\N{MALE SIGN}\N{VARIATION SELECTOR-16}"
        self.action_type = "run"
        self.label_name = "Run {}"

    async def send_response(self, interaction: discord.Interaction):
        user = interaction.user
        try:
            c = await Character.from_json(self.view.ctx, self.view.cog.config, user, self.view.cog._daily_bonus)
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            pass
        choices = self.view.cog.ACTION_RESPONSE.get(self.action_type, {})
        heroclass = getattr(c, "heroclass", {"name": "default"})["name"].lower()
        choice = random.choice(choices[heroclass])
        choice = choice.replace("$monster", self.view.challenge)
        left = getattr(c, "left")
        right = getattr(c, "right")
        if left and right:
            weapon = str(left) + str(right)
        if left and not right:
            weapon = str(left)
        if right and not left:
            weapon = str(right)
        if not left and not right:
            weapon = "fists"
        choice = choice.replace("$weapon", weapon)
        god = await self.view.cog.config.god_name()
        if await self.view.cog.config.guild(interaction.guild).god_name():
            god = await self.view.cog.config.guild(interaction.guild).god_name()
        choice = choice.replace("$god", god)
        await interaction.response.send_message(choice, ephemeral=True)

    async def callback(self, interaction: discord.Interaction):
        """Skip to previous track"""
        user = interaction.user
        for x in ["fight", "magic", "talk", "pray"]:
            if user in getattr(self.view, x, []):
                getattr(self.view, x).remove(user)
        restricted = self.view.cog.config.restrict()
        if user not in self.view.run:
            if restricted:
                all_users = []
                for (guild_id, guild_session) in self.view.cog._sessions.items():
                    guild_users_in_game = (
                        guild_session.fight
                        + guild_session.magic
                        + guild_session.talk
                        + guild_session.pray
                        + guild_session.run
                    )
                    all_users = all_users + guild_users_in_game

                if user in all_users:
                    user_id = f"{user.id}-{user.guild.id}"
                    # iterating through reactions here and removing them seems to be expensive
                    # so they can just keep their react on the adventures they can't join
                    if user_id not in self.view.cog._react_messaged:
                        await interaction.response.send_message(
                            _(
                                "**{c}**, you are already in an existing adventure. "
                                "Wait for it to finish before joining another one."
                            ).format(c=escape(user.display_name)),
                            ephemeral=True,
                        )
                        self.view.cog._react_messaged.append(user_id)
                        return
                else:
                    self.view.run.append(user)
            else:
                self.view.run.append(user)
            await self.send_response(interaction)
            await self.view.update()
        else:
            await interaction.response.send_message("You have already run from this monster.", ephemeral=True)



class GameSession(discord.ui.View):
    """A class to represent and hold current game sessions per server."""

    ctx: Context
    cog: commands.Cog
    challenge: str
    attribute: str
    timer: int
    guild: discord.Guild
    boss: bool
    miniboss: dict
    monster: dict
    message_id: int
    reacted: bool = False
    participants: Set[discord.Member] = set()
    monster_modified_stats: MutableMapping = {}
    fight: List[discord.Member] = []
    magic: List[discord.Member] = []
    talk: List[discord.Member] = []
    pray: List[discord.Member] = []
    run: List[discord.Member] = []
    message: discord.Message = None
    transcended: bool = False
    insight: Tuple[float, Character] = (0, None)
    start_time: datetime = datetime.now()
    easy_mode: bool = False
    insight = (0, None)
    no_monster: bool = False
    exposed: bool = False
    finished: bool = False

    def __init__(self, **kwargs):

        self.ctx: Context = kwargs.pop("ctx")
        self.cog: commands.Cog = kwargs.pop("cog")
        self.challenge: str = kwargs.pop("challenge")
        self.attribute: dict = kwargs.pop("attribute")
        self.guild: discord.Guild = kwargs.pop("guild")
        self.boss: bool = kwargs.pop("boss")
        self.miniboss: dict = kwargs.pop("miniboss")
        self.timer: int = kwargs.pop("timer")
        self.monster: dict = kwargs.pop("monster")
        self.monsters: Mapping[str, Mapping] = kwargs.pop("monsters", [])
        self.monster_stats: int = kwargs.pop("monster_stats", 1)
        self.monster_modified_stats = kwargs.pop("monster_modified_stats", self.monster)
        self.message = kwargs.pop("message", 1)
        self.message_id: int = 0
        self.reacted = False
        self.participants: Set[discord.Member] = set()
        self.fight: List[discord.Member] = []
        self.magic: List[discord.Member] = []
        self.talk: List[discord.Member] = []
        self.pray: List[discord.Member] = []
        self.run: List[discord.Member] = []
        self.transcended: bool = kwargs.pop("transcended", False)
        self.start_time = datetime.now()
        self.easy_mode = kwargs.get("easy_mode", False)
        self.no_monster = kwargs.get("no_monster", False)
        super().__init__(timeout=self.timer)
        self.attack_button = AttackButton(discord.ButtonStyle.grey)
        self.talk_button = TalkButton(discord.ButtonStyle.grey)
        self.magic_button = MagicButton(discord.ButtonStyle.grey)
        self.talk_button = TalkButton(discord.ButtonStyle.grey)
        self.pray_button = PrayButton(discord.ButtonStyle.grey)
        self.run_button = RunButton(discord.ButtonStyle.grey)
        self.add_item(self.attack_button)
        self.add_item(self.talk_button)
        self.add_item(self.magic_button)
        self.add_item(self.pray_button)
        self.add_item(self.run_button)

    async def update(self):
        self.attack_button.label = self.attack_button.label_name.format(f"({len(self.fight)})")
        self.talk_button.label = self.talk_button.label_name.format(f"({len(self.talk)})")
        self.magic_button.label = self.magic_button.label_name.format(f"({len(self.magic)})")
        self.pray_button.label = self.pray_button.label_name.format(f"({len(self.pray)})")
        self.run_button.label = self.pray_button.label_name.format(f"({len(self.pray)})")
        await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        """Just extends the default reaction_check to use owner_ids"""
        log.debug("Checking interaction")
        has_fund = await has_funds(interaction.user, 250)
        if not has_fund:
            await interaction.response.send_message(
                _(
                    "You contemplate going on an adventure with your friends, so "
                    "you go to your bank to get some money to prepare and they "
                    "tell you that your bank is empty!\n"
                    "You run home to look for some spare coins and you can't "
                    "even find a single one, so you tell your friends that you can't "
                    "join them as you already have plans... as you are too embarrassed "
                    "to tell them you are broke!"
                ),
                ephemeral=True
            )
            return False
        return True
