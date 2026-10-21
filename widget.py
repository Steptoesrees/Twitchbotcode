import asyncio
import json


class websocket_server:
    def __init__(self):
        self.widget_clients = set()

    async def widget_connection(self, ws):
        self.widget_clients.add(ws)
        try:
            await ws.send(json.dumps({'type': 'tasks', 'tasks': ''}))
            await ws.wait_closed()
        finally:
            self.widget_clients.discard(ws)


    def broadcast(self, payload):
        msg = json.dumps(payload)
        for client in list(self.widget_clients):
            asyncio.ensure_future(client.send(msg))


    def broadcast_tasks(self, task_list):
        self.broadcast({'type': 'tasks', 'tasks': task_list})


    def broadcast_task_completed(self, task):
        self.broadcast({'type': 'taskCompleted', 'task': task})
