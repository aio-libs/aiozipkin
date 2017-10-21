from .helpers import (
    CLIENT,
    CLIENT_RECEIVED,
    CLIENT_SEND,
    SERVER,
    SERVER_RECEIVED,
    SERVER_SEND,
    PRODUCER,
    CONSUMER,
)


class Record:

    def __init__(self, context, local_endpoint):
        self._context = context
        self._local_endpoint = local_endpoint._asdict()
        self._finished = False

        self._name = 'unknown'
        self._kind = None
        self._timestamp = None
        self._duration = None
        self._remote_endpoint = None
        self._annotations = []
        self._tags = {}

    def start(self, ts):
        self._timestamp = ts
        return self

    def finish(self, ts):
        if self._finished:
            return self
        if ts is not None and self._kind not in (PRODUCER, CONSUMER):
            self._duration = max(ts - self._timestamp, 1)
        self._finished = True
        return self

    def name(self, n):
        self._name = n
        return self

    def set_tag(self, key, value):
        self._tags[key] = value
        return self

    def annotate(self, value, ts):
        if value == CLIENT_SEND:
            self.kind(CLIENT)
            self._timestamp = ts
        elif value == SERVER_RECEIVED:
            self.kind(SERVER)
            self._timestamp = ts
        elif value == CLIENT_RECEIVED:
            self.kind(CLIENT)
            self.finish(ts)
        elif value == SERVER_SEND:
            self.kind(SERVER)
            self.finish(ts)
        else:
            v = {'value': value, 'timestamp': int(ts)}
            self._annotations.append(v)
        return self

    def kind(self, kind):
        self._kind = kind
        return self

    def remote_endpoint(self, endpoint):
        self._remote_endpoint = endpoint._asdict()
        return self

    def asdict(self):
        c = self._context
        rec = {
            'traceId': c.trace_id,
            'name': self._name,
            'parentId': c.parent_id,
            'id': c.span_id,
            'kind': self._kind,
            'timestamp': self._timestamp,
            'duration': self._duration,
            'debug': c.debug,
            'shared': c.shared,
            'localEndpoint': self._local_endpoint,
            'remoteEndpoint': self._remote_endpoint,
            'annotations': self._annotations,
            'tags': self._tags,
        }
        return rec
