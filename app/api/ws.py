from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.alert_broadcaster import broadcaster

router = APIRouter()


@router.websocket("/alertas")
async def websocket_alertas(websocket: WebSocket):
    await websocket.accept()
    queue = await broadcaster.connect()
    try:
        while True:
            payload = await queue.get()
            try:
                await websocket.send_text(payload)
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.disconnect(queue)
