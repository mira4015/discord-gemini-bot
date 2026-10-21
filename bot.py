import os
import threading
import http.server
import socketserver
import discord
import aiohttp

# ---------------------------------------------------------
# RenderのFreeプラン（Web Service）でポートタイムアウトを防ぐためのダミーサーバー
# ---------------------------------------------------------
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ---------------------------------------------------------
# Discord Bot 設定
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True  # Message Content Intent

client = discord.Client(intents=intents)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY")

@client.event
async def on_ready():
    print(f"ログインしました: {client.user}")

@client.event
async def on_message(message):
    # 自分自身（Gemini Bot自身）の発言は無限ループ防止のため無視
    if message.author.id == client.user.id:
        return

    # 受信メッセージをログ出力
    print(f"[Message Received] Author: {message.author}, Content: '{message.content}'")

    # メッセージ本文に「ゲミナイ」が含まれているか判別（プレフィックス判定）
    # ※DiscordSRV経由の場合「<m4ru_ha> ゲミナイ テスト」や「m4ru_ha: ゲミナイ テスト」の形式で届くため in 判定を行っています
    if "ゲミナイ" in message.content:
        print("[Match] 'ゲミナイ' を検知しました。")
        
        # 「ゲミナイ」以降の文字列を質問文として抽出
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
                            # ログチャンネルへ返信（DiscordSRVが自動でマイクラ内へ転送します）
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
