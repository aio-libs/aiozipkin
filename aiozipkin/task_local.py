import asyncio


class TaskLocalManager:
    def __init__(self, default=None):
        self.stack = []
        self.default = default

    def push(self, info):
        self.stack.append(info)

    set = push

    def pop(self):
        if self.stack:
            return self.stack.pop()

    def get(self):
        try:
            return self.stack[-1]
        except IndexError:
            return self.default

    def clear(self):
        self.stack[:] = []

    @property
    def top(self):
        try:
            return self.stack[-1]
        except (AttributeError, IndexError):
            return self.default


def set_task_ctx(key, value):
    # TODO: check current task is not none
    t = asyncio.Task.current_task()
    if not hasattr(t, '_context'):
        t._context = TaskLocalManager()
    t._context.push(key, value)


def get_task_ctx(key):
    # TODO: check current task is not none
    t = asyncio.Task.current_task()
    if not hasattr(t, '_context'):
        t._context = TaskLocalManager()
    return t._context.pop(key)
