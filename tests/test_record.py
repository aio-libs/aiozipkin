from aiozipkin.record import Record
from aiozipkin.helpers import TraceContext, Endpoint


def test_basic_ctr():
    context = TraceContext("string", "string", "string", True, True, True)
    local_endpoint = Endpoint("string", "string", "string", 0)
    remote_endpoint = Endpoint("string", "string", "string", 0)
    record = (Record(context, local_endpoint)
              .start(0)
              .name("string")
              .set_tag("additionalProp1", "string")
              .set_tag("additionalProp2", "string")
              .set_tag("additionalProp3", "string")
              .kind("CLIENT")
              .annotate("string", 0)
              .remote_endpoint(remote_endpoint)
              .finish(0)
              )
    dict_record = record.asdict()
    expected = {
        "traceId": "string",
        "name": "string",
        "parentId": "string",
        "id": "string",
        "kind": "CLIENT",
        "timestamp": 0,
        "duration": 1,
        "debug": True,
        "shared": True,
        "localEndpoint": {
          "serviceName": "string",
          "ipv4": "string",
          "ipv6": "string",
          "port": 0
        },
        "remoteEndpoint": {
          "serviceName": "string",
          "ipv4": "string",
          "ipv6": "string",
          "port": 0
        },
        "annotations": [
          {
            "timestamp": 0,
            "value": "string"
          }
        ],
        "tags": {
          "additionalProp1": "string",
          "additionalProp2": "string",
          "additionalProp3": "string"
        }
      }
    assert dict_record == expected
