import os
import threading
import http.server
import socketserver
import discord
import aiohttp

# RenderなどのWebサービスで必須となるポートバインド用ダミーサーバー
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

# 別スレッドでダミーサーバーをバックグラウンド起動
threading.Thread(target=run_dummy_server, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True

# ★修正：@client.eventより先にclientを定義する
client = discord.Client(intents=intents)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY")

@client.event
async def on_ready():
    print(f"ログインしました: {client.user}")

@client.event
async def on_message(message):
    # 自分自身のメッセージは無視
    if message.author.id == client.user.id:
        return

    print(f"[Message Received] Author: {message.author}, Content: '{message.content}'")

    # メッセージ内に「ゲミナイ」が含まれているか判定
    if "ゲミナイ" in message.content:
        print("[Match] 'ゲミナイ' を検知しました。")
        
        idx = message.content.find("ゲミナイ")
        user_input = message.content[idx + 4:].strip()
        print(f"[Extracted Query] '{user_input}'")
        
        if not user_input:
            await message.channel.send("質問内容を入力してください。（例: `ゲミナイ かまどの作り方は？`）")
            return

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
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.dify.ai/v1/chat-messages",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            answer = data.get("answer", "返答を取得できませんでした。")
                            await message.channel.send(answer)
                        else:
                            error_text = await response.text()
                            print(f"[Dify API Error] Code: {response.status}, Response: {error_text}")
                            await message.channel.send("エラーが発生しました。Difyの設定を確認してください。")

        except Exception as e:
            print(f"[Exception Error] {e}")
            await message.channel.send("処理中にエラーが発生しました。")

if __name__ == "__main__":
    if DISCORD_TOKEN:
        client.run(DISCORD_TOKEN)
    else:
        print("エラー: DISCORD_TOKEN が設定されていません。")
