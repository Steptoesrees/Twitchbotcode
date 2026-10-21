from typing import TYPE_CHECKING

import twitch

if TYPE_CHECKING:
    from widget import websocket_server


class TaskList:
    def __init__(self, widget_server) -> None:
        self.widget_server: websocket_server = widget_server
        self.task_list = []
        self.tasknum = 0


    def get_tasks(self, chatter_name):
        tasks = ''.join(' | ' + t['task'] for t in self.task_list if t['user'] == chatter_name)
        return tasks or 'you have no task'


    async def add_task(self, chatter_name, task_name, msg_id):
        if any(t['user'] == chatter_name and t['task'].lower() == task_name.lower() and not t['done'] for t in self.task_list):
            await twitch.send_chat_message('You already made this task 0.o', parent_id=msg_id)
        else:
            self.task_list.append({'user': chatter_name, 'task': task_name, 'done': False, 'taskNum': self.tasknum})
            self.tasknum += 1
            await twitch.send_chat_message(f'{task_name} Added!', parent_id=msg_id)
        self.widget_server.broadcast_tasks(self.task_list)


    async def delete_task(self, chatter_name, task_name, msg_id):
        self.task_list = [t for t in self.task_list if not (t['user'] == chatter_name and t['task'].lower() == task_name.lower())]
        self.widget_server.broadcast_tasks(self.task_list)
        await twitch.send_chat_message(f'{task_name} Deleted!', parent_id=msg_id)


    async def complete_task(self, chatter_name, task_name, msg_id):
        found = False
        for t in self.task_list:
            if t['user'] == chatter_name and t['task'].lower() == task_name.lower() and not t['done']:
                t['done'] = True
                found = True
                self.widget_server.broadcast_tasks(self.task_list)
                self.widget_server.broadcast_task_completed({'user': chatter_name, 'task': task_name, 'taskNum': t['taskNum']})
                await twitch.send_chat_message(f'{task_name} Finished!', parent_id=msg_id)
        if not found:
            if any(t['user'] == chatter_name and t['task'] == task_name and t['done'] for t in self.task_list):
                await twitch.send_chat_message('You already completed this task :o', parent_id=msg_id)
            else:
                await twitch.send_chat_message(f"You don't have this task :(... Here is a list of your tasks: {self.get_tasks(chatter_name)}", parent_id=msg_id)
