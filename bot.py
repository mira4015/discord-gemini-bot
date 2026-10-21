import os
import discord
from discord.ext import commands
import requests

# Renderの環境変数から読み込み
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
DIFY_API_KEY = os.environ.get('DIFY_API_KEY')
DIFY_API_URL = 'https://api.dify.ai/v1/chat-messages'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'ログインしました: {bot.user.name}')

@bot.command()
async def gemini(ctx, *, message):
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        "inputs": {},
        "query": message,
        "response_mode": "blocking",
        "user": str(ctx.author.id)
    }
    
    async with ctx.typing():
        response = requests.post(DIFY_API_URL, headers=headers, json=data)
        result = response.json()
        answer = result.get('answer', 'エラーが発生しました')
        
    await ctx.send(answer)

bot.run(DISCORD_TOKEN)
