import os
import threading
import http.server
import socketserver
import discord
import requests

# ---------------------------------------------------------
# RenderのFreeプラン（Web Service）でポートタイムアウトを防ぐためのダミーサーバー
# ---------------------------------------------------------
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

# ダミーサーバーをバックグラウンドで起動
threading.Thread(target=run_dummy_server, daemon=True).start()

# ---------------------------------------------------------
# Discord Bot 設定
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True  # 特権インテント（Message Content Intent）

client = discord.Client(intents=intents)

# 環境変数の取得
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY")

@client.event
async def on_ready():
    print(f"ログインしました: {client.user}")

@client.event
async def on_message(message):
    # Bot自身の発言には反応しない
    if message.author == client.user:
        return

    # コマンド判定 (ゲミナイ から始まるメッセージ)
    if message.content.startswith("ゲミナイ"):
        # プロンプトの抽出 ("ゲミナイ" の4文字分をカット)
        user_input = message.content[4:].strip()
        
        if not user_input:
            await message.channel.send("質問内容を入力してください。（例: `ゲミナイ こんにちは`）")
            return

        # Dify API へのリクエスト処理
        headers = {
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": {},
            "query": user_input,
            "response_mode": "blocking",
            "user": f"discord_{message.author.id}"
        }

        try:
            async with message.channel.typing():
                response = requests.post(
                    "https://api.dify.ai/v1/chat-messages",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "返答を取得できませんでした。")
                    await message.channel.send(answer)
                else:
                    print(f"Dify API Error: {response.status_code} - {response.text}")
                    await message.channel.send("エラーが発生しました。Difyの設定やAPIキーを確認してください。")

        except Exception as e:
            print(f"Exception: {e}")
            await message.channel.send("処理中にエラーが発生しました。")

# Botの起動
if __name__ == "__main__":
    if DISCORD_TOKEN:
        client.run(DISCORD_TOKEN)
    else:
        print("エラー: DISCORD_TOKEN が設定されていません。")
