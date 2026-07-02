import asyncio
import websockets
import json

PORT = 55555
clients = {}

# 模擬資料庫
USER_DB = {
    "admin": "1234"
}

async def broadcast(message_dict):
    """廣播 JSON 訊息給所有人"""
    if clients:
        message_json = json.dumps(message_dict)
        await asyncio.gather(*[client.send(message_json) for client in clients])

async def handle_client(websocket):
    nickname = None
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")

            # 1. 處理註冊
            if action == "REGISTER":
                u, p = data["username"], data["password"]
                if u in USER_DB:
                    await websocket.send(json.dumps({"type": "REG_FAIL", "msg": "帳號已被註冊"}))
                elif not u or not p:
                    await websocket.send(json.dumps({"type": "REG_FAIL", "msg": "帳號密碼不可為空"}))
                else:
                    USER_DB[u] = p
                    await websocket.send(json.dumps({"type": "REG_SUCCESS"}))

            # 2. 處理成員登入
            elif action == "LOGIN":
                u, p = data["username"], data["password"]
                if u in USER_DB and USER_DB[u] == p:
                    nickname = f"{u}(成員)"
                    clients[websocket] = nickname
                    await websocket.send(json.dumps({"type": "AUTH_SUCCESS", "nickname": nickname}))
                    await broadcast({"type": "SYSTEM", "msg": f"【系統】:{nickname} 加入了聊天室！"})
                else:
                    await websocket.send(json.dumps({"type": "AUTH_FAIL", "msg": "帳號或密碼錯誤"}))

            # 3. 處理訪客進入
            elif action == "GUEST":
                g = data["guest_name"] or "神祕路人"
                nickname = f"{g}(訪客)"
                clients[websocket] = nickname
                await websocket.send(json.dumps({"type": "AUTH_SUCCESS", "nickname": nickname}))
                await broadcast({"type": "SYSTEM", "msg": f"【系統】:{nickname} 加入了聊天室！"})

            # 4. 處理聊天訊息
            elif action == "CHAT":
                if websocket in clients:
                    await broadcast({
                        "type": "MSG",
                        "sender": clients[websocket],
                        "content": data["content"]
                    })

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # 當任何電腦斷線（包含關閉網頁、斷網），這裡會自動觸發並通知所有人
        if websocket in clients:
            nickname = clients[websocket]
            del clients[websocket]
            await broadcast({"type": "SYSTEM", "msg": f"【系統】:{nickname} 離開了聊天室！"})

async def main():
    # 綁定 "0.0.0.0"：允許來自其他電腦（非本機）的 WebSocket 連線
    print(f"WebSocket 伺服器正在 port {PORT} 啟動，允許外部連線...")
    async with websockets.serve(handle_client, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())