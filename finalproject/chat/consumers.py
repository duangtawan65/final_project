# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    connected_users = {}  # เก็บจำนวนผู้ใช้ในแต่ละห้อง

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # เพิ่มผู้ใช้เข้าห้อง
        if self.room_id not in self.connected_users:
            self.connected_users[self.room_id] = 1
        else:
            self.connected_users[self.room_id] += 1

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # แจ้งสถานะห้องแชท
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_status",
                "status": "connected",
                "users_count": self.connected_users[self.room_id]
            }
        )

    async def disconnect(self, close_code):
        # ลดจำนวนผู้ใช้ในห้อง
        if self.room_id in self.connected_users:
            self.connected_users[self.room_id] -= 1
            if self.connected_users[self.room_id] <= 0:
                del self.connected_users[self.room_id]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_status",
                "status": "disconnected",
                "users_count": self.connected_users.get(self.room_id, 0)
            }
        )

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = text_data_json["username"]

        # ส่งข้อความเมื่อมีผู้ใช้ครบ 2 คน
        if self.connected_users.get(self.room_id, 0) == 2:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "username": username
                }
            )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))

    async def chat_status(self, event):
        # ส่งสถานะห้องแชท
        await self.send(text_data=json.dumps({
            'type': 'status',
            'status': event['status'],
            'users_count': event['users_count']
        }))