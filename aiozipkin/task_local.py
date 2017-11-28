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


def _get_or_create_stack(key):
    t = asyncio.Task.current_task()
    if not hasattr(t, key):
        stack = TaskLocalManager()
        setattr(t, key, stack)
    else:
        stack = getattr(t, key)
    return stack


def set_task_ctx(key, value):
    stack = _get_or_create_stack(key)
    return stack.push(value)


def get_task_ctx(key):
    stack = _get_or_create_stack(key)
    return stack.get()


def pop_task_ctx(key):
    stack = _get_or_create_stack(key)
    return stack.pop()
