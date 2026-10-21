import os
import threading
from flask import Flask
import discord
from discord.ext import commands
import requests

# --------------------------------------------------
# Render無料枠(Web Service)用 ポート開放ヘルスチェック
# --------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web_server():
    # Renderが割り当てるPORT番号を取得（デフォルト8080）
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# スレッドでダミーWebサーバーを起動
threading.Thread(target=run_web_server, daemon=True).start()

# --------------------------------------------------
# Discord Bot 処理（ステートレス・一問一答型）
# --------------------------------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "YOUR_DIFY_API_KEY")
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1/chat-messages")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        user_query = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()

        if not user_query:
            await message.channel.send("質問内容を入力してください。")
            return

        async with message.channel.typing():
            try:
                headers = {
                    "Authorization": f"Bearer {DIFY_API_KEY}",
                    "Content-Type": "application/json"
                }

                # 一問一答形式（conversation_idなし）
                payload = {
                    "inputs": {},
                    "query": user_query,
                    "response_mode": "blocking",
                    "user": str(message.author.id)
                }

                response = requests.post(DIFY_API_URL, json=payload, headers=headers, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "回答を取得できませんでした。")
                    await message.reply(answer)
                else:
                    print(f"Dify API Error: {response.status_code} - {response.text}")
                    await message.reply("エラーが発生しました。Difyの設定やAPIキーを確認してください。")

            except Exception as e:
                print(f"Exception: {e}")
                await message.reply("通信エラーが発生しました。しばらく経ってからやり直してください。")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
