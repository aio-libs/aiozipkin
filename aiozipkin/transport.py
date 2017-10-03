import json
import requests


# TODO: make transport async
class Transport:

    def __init__(self, address):
        self._address = address or 'http://localhost:9411/api/v2/spans'

    def send(self, record):
        data = [record.asdict()]
        self.http_transport(data)

    def http_transport(self, body):
        data = json.dumps(body, indent=True)
        print(data)
        resp = requests.post(
            self._address,
            data=data,
            headers={'Content-Type': 'application/json'})
        print(resp)
        print(resp.content)
