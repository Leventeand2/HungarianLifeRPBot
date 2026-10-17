import hmac
import os

import discord
from aiohttp import web
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.environ["GUILD_ID"])
API_SECRET = os.environ["API_SECRET"]
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("PORT", os.environ.get("API_PORT", "3000")))

if not TOKEN:
    raise ValueError("DISCORD_TOKEN was not found in your .env file!")


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="", intents=discord.Intents.default())
        self.runner: web.AppRunner | None = None

    async def setup_hook(self):
        await self.tree.sync()

        app = web.Application()
        app.add_routes([
            web.get("/", self.home),
            web.get("/check/{discord_id}", self.check_member),
        ])
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, API_HOST, API_PORT)
        await site.start()
        print(f"Web server listening on {API_HOST}:{API_PORT}")

    async def close(self):
        if self.runner:
            await self.runner.cleanup()
        await super().close()

    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def home(self, request: web.Request) -> web.Response:
        return web.Response(text="Bot is running!")

    async def check_member(self, request: web.Request) -> web.Response:
        key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(key, API_SECRET):
            return web.json_response({"error": "unauthorized"}, status=401)

        discord_id = request.match_info["discord_id"]
        if not discord_id.isdigit():
            return web.json_response({"error": "invalid id"}, status=400)

        guild = self.get_guild(GUILD_ID)
        if guild is None:
            return web.json_response({"error": "guild unavailable"}, status=503)

        uid = int(discord_id)
        member = guild.get_member(uid)
        if member is None:
            try:
                member = await guild.fetch_member(uid)
            except discord.NotFound:
                return web.json_response({"in_guild": False})
            except discord.HTTPException:
                return web.json_response({"error": "discord error"}, status=502)

        return web.json_response({"in_guild": True, "username": member.name})


bot = Bot()


@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


bot.run(TOKEN)