from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from discord import File
from discord.ext.commands import Cog, command, param
from jishaku.codeblocks import Codeblock, codeblock_converter

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from .. import ReplBot


class REPL(
    Cog,
    name = "REPL",
    description = "REPL (Read, Eval, Print, Loop) commands.",
):
    def __init__(self, bot: ReplBot) -> None:
        self.bot = bot

    @command(
        aliases = ("run", "repl"),
        brief = "Runs V code.",
        help = "Runs V code."
    )
    async def eval(
        self,
        ctx: Context,
        *,
        code: Codeblock | None = param(converter = codeblock_converter, default = None)
    ) -> None:
        if code is None:
            await ctx.reply("No code provided.")
            return

        async with await self.bot.session.post(
            "https://play.vlang.io/run",
            data = { "code": code.content },
        ) as response:
            text = await response.text()
            text = text.replace("`", "\u200B`\u200B")  # Zero-width space.

            if len(text) + 6 > 2000:
                await ctx.reply(
                    "The output was too long to be sent as a message. Here is a file instead:",
                    file = File(BytesIO(text.encode()), filename = "output.txt")
                )
                return

            await ctx.reply(
                "```" + text + "```"
            )

    @command(
        aliases = ("download",),
        brief = "Shows the code in a V playground query.",
        help = "Shows the code in a V playground query."
    )
    async def show(self, ctx: Context, query: str | None = None) -> None:
        if query is None:
            if not (reply := ctx.message.reference):
                await ctx.reply("No query provided.")
                return

            replied_message = await ctx.channel.fetch_message(reply.message_id)
            content = replied_message.content

            if "play.vlang.io/?query=" in content:
                query = content.split("play.vlang.io/?query=", 1)[1].split(" ", 1)[0]
            else:
                query = content.split(" ", 1)[0]

        query = query.lstrip("https://").lstrip("play.vlang.io/?query=")

        if not query:
            await ctx.reply("No query provided.")
            return

        async with await self.bot.session.post(
            f"https://play.vlang.io/query",
            data = { "hash": query }
        ) as response:
            text = await response.text()

            if text == "Not found.":
                await ctx.reply("Invalid link.")
                return

            if len(text) + 8 > 2000:
                await ctx.reply(
                    "The code was too long to be sent as a message. Here is a file instead:",
                    file = File(BytesIO(text.encode()), filename = "code.v")
                )
                return

            await ctx.reply(
                "```v\n" + text + "```"
            )


async def setup(bot: ReplBot) -> None:
    await bot.add_cog(REPL(bot))