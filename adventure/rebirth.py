# -*- coding: utf-8 -*-
import asyncio
import logging
import time

from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import box, humanize_number
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

from .abc import AdventureMixin
from .bank import bank
from .charsheet import Character, has_funds
from .helpers import escape, smart_embed

_ = Translator("Adventure", __file__)

log = logging.getLogger("red.cogs.adventure")


class RebirthCommands(AdventureMixin):
    @commands.command()
    @commands.bot_has_permissions(add_reactions=True)
    @commands.guild_only()
    async def rebirth(self, ctx: commands.Context):
        """Resets your character level and increases your rebirths by 1."""
        if self.in_adventure(ctx):
            return await smart_embed(ctx, _("You tried to rebirth but the monster ahead is commanding your attention."))
        if not await self.allow_in_dm(ctx):
            return await smart_embed(ctx, _("This command is not available in DM's on this bot."))
        async with self.get_lock(ctx.author):
            try:
                c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
            except Exception as exc:
                log.exception("Error with the new character sheet", exc_info=exc)
                return
            if c.lvl < c.maxlevel:
                return await smart_embed(ctx, _("You need to be level `{c.maxlevel}` to rebirth.").format(c=c))
            if not c.last_currency_check + 10 < time.time():
                return await smart_embed(ctx, _("You need to wait a little before rebirthing.").format(c=c))
            if not await bank.is_global():
                rebirth_cost = await self.config.guild(ctx.guild).rebirth_cost()
            else:
                rebirth_cost = await self.config.rebirth_cost()
            rebirthcost = 1000 * c.rebirths
            current_balance = c.bal
            last_known_currency = c.last_known_currency
            if last_known_currency and current_balance / last_known_currency < 0.25:
                currency_name = await bank.get_currency_name(
                    ctx.guild,
                )
                return await smart_embed(
                    ctx,
                    _(
                        "You tried to get rid of all your {currency_name} -- tsk tsk, "
                        "once you get back up to {cur} {currency_name} try again."
                    ).format(
                        currency_name=currency_name,
                        cur=humanize_number(last_known_currency),
                    ),
                )
            else:
                has_fund = await has_funds(ctx.author, rebirthcost)
            if not has_fund:
                currency_name = await bank.get_currency_name(
                    ctx.guild,
                )
                return await smart_embed(
                    ctx,
                    _("You need more {currency_name} to be able to rebirth.").format(currency_name=currency_name),
                )
            space = "\N{EN SPACE}"
            open_msg = await smart_embed(
                ctx,
                _(
                    f"Rebirthing will:\n\n"
                    f"* cost {int(rebirth_cost)}% of your credits\n"
                    f"* cost all of your current gear\n"
                    f"{space*4}- Legendary and Ascended items lose one degradation "
                    f"point per rebirth and are broken down when they have 0 left.\n"
                    f"{space*4}- Set items never disappear\n"
                    f"* set you back to level 1 while keeping your current class\n\n"
                    f"In turn, rebirthing will give you a higher stat base, a better chance "
                    f"for acquiring more powerful items, a higher max level, and the "
                    f"ability to convert chests to higher rarities after the second rebirth.\n\n"
                    f"Would you like to rebirth?"
                ),
            )
            start_adding_reactions(open_msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(open_msg, ctx.author)
            try:
                await ctx.bot.wait_for("reaction_add", check=pred, timeout=60)
            except asyncio.TimeoutError:
                await self._clear_react(open_msg)
                return await smart_embed(ctx, "I can't wait forever, you know.")
            else:
                if not pred.result:
                    await open_msg.edit(
                        content=box(
                            _("{c} decided not to rebirth.").format(c=escape(ctx.author.display_name)),
                            lang="css",
                        ),
                        embed=None,
                    )
                    return await self._clear_react(open_msg)

                try:
                    c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
                except Exception as exc:
                    log.exception("Error with the new character sheet", exc_info=exc)
                    return
                if c.lvl < c.maxlevel:
                    await open_msg.edit(
                        content=box(
                            _("You need to be level `{c}` to rebirth.").format(c=c.maxlevel),
                            lang="css",
                        ),
                        embed=None,
                    )
                    return
                bal = await bank.get_balance(ctx.author)
                if bal >= 1000:
                    withdraw = int((bal - 1000) * (rebirth_cost / 100.0))
                    await bank.withdraw_credits(ctx.author, withdraw)
                else:
                    withdraw = int(bal * (rebirth_cost / 100.0))
                    await bank.set_balance(ctx.author, 0)

                await open_msg.edit(
                    content=box(
                        _("{c}, congratulations on your rebirth.\nYou paid {bal}.").format(
                            c=escape(ctx.author.display_name),
                            bal=humanize_number(withdraw),
                        ),
                        lang="css",
                    ),
                    embed=None,
                )
                await self.config.user(ctx.author).set(await c.rebirth())
