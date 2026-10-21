import os
import threading
import http.server
import socketserver
import discord
import aiohttp  # 非同期HTTPリクエスト用に変更

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
    # 自分自身（Gemini Bot自身）の発言だけを無視する
    if message.author.id == client.user.id:
        return

    # 受信メッセージをログに出力（logMonなどの他のBotの発言も出力されます）
    print(f"[Message Received] Author: {message.author} (Bot: {message.author.bot}), Content: '{message.content}'")

    # コマンド判定 (ゲミナイ から始まるメッセージ)
    if message.content.startswith("ゲミナイ"):
        print("[Match] 'ゲミナイ' コマンドを検知しました。")
        
        # プロンプトの抽出 ("ゲミナイ" の4文字分をカット)
        user_input = message.content[4:].strip()
        print(f"[Extracted Query] '{user_input}'")
        
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
                # aiohttp を使って非同期で Dify API を呼び出す（タイムアウト回避）
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
                            await message.channel.send("エラーが発生しました。Difyの設定やAPIキーを確認してください。")

        except Exception as e:
            print(f"[Exception Error] {e}")
            await message.channel.send("処理中にエラーが発生しました。")

# Botの起動
if __name__ == "__main__":
    if DISCORD_TOKEN:
        client.run(DISCORD_TOKEN)
    else:
        print("エラー: DISCORD_TOKEN が設定されていません。")
