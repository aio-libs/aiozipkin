import asyncio
from typing import Any

import aiohttp
import pytest
from aiodocker import Docker
from async_generator import async_generator, yield_


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--no-pull", action="store_true", default=False, help=("Force docker pull")
    )


@pytest.fixture(scope="session")  # type: ignore[misc]
def docker_pull(request: Any) -> bool:
    return not request.config.getoption("--no-pull")


@pytest.fixture(scope="session")  # type: ignore[misc]
@async_generator  # type: ignore[misc]
async def docker() -> Any:
    client = Docker()
    await yield_(client)
    await client.close()


async def wait_for_response(url: str, delay: float = 0.001) -> None:
    last_error = None
    async with aiohttp.ClientSession() as session:
        for _ in range(100):
            try:
                async with session.get(url) as response:
                    data = await response.text()
                    assert response.status < 500, data
                break
            except (aiohttp.ClientError, AssertionError) as e:
                last_error = e
                await asyncio.sleep(delay)
                delay *= 2
        else:
            pytest.fail(f"Cannot start server: {last_error}")


@pytest.fixture(scope="session")  # type: ignore[misc]
@async_generator  # type: ignore[misc]
async def zipkin_server(docker: Docker, docker_pull: bool) -> Any:
    tag = "2"
    image = f"openzipkin/zipkin:{tag}"
    host = "127.0.0.1"

    if docker_pull:
        print(f"Pulling {image} image")
        await docker.pull(image)

    container = await docker.containers.create_or_replace(
        name=f"zipkin-server-{tag}",
        config={
            "Image": image,
            "AttachStdout": False,
            "AttachStderr": False,
            "HostConfig": {"PublishAllPorts": True},
        },
    )
    await container.start()
    port = (await container.port(9411))[0]["HostPort"]

    params = dict(host=host, port=port)

    url = f"http://{host}:{port}"
    await wait_for_response(url)

    await yield_(params)

    await container.kill()
    await container.delete(force=True)


@pytest.fixture  # type: ignore[misc]
def zipkin_url(zipkin_server: Any) -> str:
    url = "http://{host}:{port}/api/v2/spans".format(**zipkin_server)
    return url


@pytest.fixture(scope="session")  # type: ignore[misc]
@async_generator  # type: ignore[misc]
async def jaeger_server(docker: Docker, docker_pull: bool) -> Any:
    # docker run -d -e COLLECTOR_ZIPKIN_HTTP_PORT=9411 \
    # -p5775:5775/udp -p6831:6831/udp -p6832:6832/udp \
    # -p5778:5778 -p16686:16686 -p14268:14268
    # -p9411:9411 jaegertracing/all-in-one:latest

    tag = "1.0.0"
    image = f"jaegertracing/all-in-one:{tag}"
    host = "127.0.0.1"

    if docker_pull:
        print(f"Pulling {image} image")
        await docker.pull(image)

    container = await docker.containers.create_or_replace(
        name=f"jaegertracing-server-{tag}",
        config={
            "Image": image,
            "AttachStdout": False,
            "AttachStderr": False,
            "HostConfig": {"PublishAllPorts": True},
            "Env": ["COLLECTOR_ZIPKIN_HTTP_PORT=9411"],
            "ExposedPorts": {
                "14268/tcp": {},
                "16686/tcp": {},
                "5775/udp": {},
                "5778/tcp": {},
                "6831/udp": {},
                "6832/udp": {},
                "9411/tcp": {},
            },
        },
    )
    await container.start()

    zipkin_port = (await container.port(9411))[0]["HostPort"]
    jaeger_port = (await container.port(16686))[0]["HostPort"]
    params = dict(host=host, zipkin_port=zipkin_port, jaeger_port=jaeger_port)

    url = f"http://{host}:{zipkin_port}"
    await wait_for_response(url)

    await yield_(params)

    await container.kill()
    await container.delete(force=True)


@pytest.fixture  # type: ignore[misc]
def jaeger_url(jaeger_server: Any) -> str:
    url = "http://{host}:{zipkin_port}/api/v2/spans".format(**jaeger_server)
    return url


@pytest.fixture  # type: ignore[misc]
def jaeger_api_url(jaeger_server: Any) -> str:
    return "http://{host}:{jaeger_port}".format(**jaeger_server)
