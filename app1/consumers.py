import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Projects, Task

User = get_user_model()


class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.project_group_name = f'tasks_{self.project_id}'

        await self.channel_layer.group_add(
            self.project_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.project_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'task_update':
            await self.channel_layer.group_send(
                self.project_group_name,
                {
                    'type': 'task_update',
                    'task': text_data_json['task']
                }
            )

    async def task_update(self, event):
        task = event['task']

        await self.send(text_data=json.dumps({
            'type': 'task_update',
            'task': task
        }))


@database_sync_to_async
def get_project_user(project_id):
    try:
        project = Projects.objects.get(id=project_id)
        return project.user
    except Projects.DoesNotExist:
        return None


def send_task_update(project_id, task_data):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'tasks_{project_id}',
        {
            'type': 'task_update',
            'task': task_data
        }
    )