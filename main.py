
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))


Thread(target=run).start()


load_dotenv()

class Bot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}")


intents = discord.Intents.default()
bot = Bot(command_prefix="!", intents=intents)


@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


token = os.getenv("DISCORD_TOKEN")

if not token:
    raise ValueError("DISCORD_TOKEN was not found in your .env file!")

bot.run(token)
