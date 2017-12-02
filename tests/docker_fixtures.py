import asyncio

import aiohttp
import pytest
from aiodocker import Docker
from async_generator import yield_, async_generator


def pytest_addoption(parser):
    parser.addoption('--no-pull', action='store_true', default=False,
                     help=('Force docker pull'))


@pytest.fixture(scope='session')
def docker_pull(request):
    return not request.config.getoption('--no-pull')


@pytest.fixture(scope='session')
@async_generator
async def docker():
    client = Docker()
    await yield_(client)
    await client.close()


@pytest.fixture(scope='session')
@async_generator
async def zipkin_server(docker, docker_pull):
    tag = '2'
    image = 'openzipkin/zipkin:{}'.format(tag)
    host = '127.0.0.1'

    if docker_pull:
        print('Pulling {} image'.format(image))
        await docker.pull(image)

    container = await docker.containers.create_or_replace(
        name='zipkin-server-{tag}'.format(tag=tag),
        config={
            'Image': image,
            'AttachStdout': False,
            'AttachStderr': False,
            'HostConfig': {
                'PublishAllPorts': True,
            },
        }
    )
    await container.start()
    port = (await container.port(9411))[0]['HostPort']

    params = dict(host=host, port=port)

    delay = 0.001
    last_error = None
    url = 'http://{}:{}'.format(host, port)

    async with aiohttp.ClientSession() as session:
        for i in range(100):
            try:
                async with session.get(url) as response:
                    await response.text()
                break
            except aiohttp.ClientError as e:
                last_error = e
                await asyncio.sleep(delay)
                delay *= 2
        else:
            pytest.fail('Cannot start zipkin server: {}'.format(last_error))

    await yield_(params)

    await container.kill()
    await container.delete(force=True)


@pytest.fixture
def zipkin_url(zipkin_server):
    return 'http://{host}:{port}'.format(**zipkin_server)
