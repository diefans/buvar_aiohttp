import pytest


# running in manylinux docker
# the loop fixture in buvar.testing seem to have no effect
@pytest.fixture
def loop(event_loop):
    return event_loop


@pytest.mark.asyncio
@pytest.mark.buvar_plugins("buvar.config")
async def test_app_dummy(buvar_aiohttp_app, aiohttp_client, caplog):
    import aiohttp.web
    import logging

    async def hello(request):
        return aiohttp.web.Response(body=b"Hello, world")

    buvar_aiohttp_app.router.add_route("GET", "/", hello)

    caplog.set_level(logging.DEBUG)
    client = await aiohttp_client(buvar_aiohttp_app)
    resp = await client.get("/")
    assert "Hello, world" == await resp.text()
    assert caplog


def test_structure_config():
    import socket
    import buvar_aiohttp

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        source = {"sock": s.fileno()}
        config = buvar_aiohttp.config.relaxed_converter.structure(
            source, buvar_aiohttp.AioHttpConfig
        )
        assert isinstance(config.sock, socket.socket)
    finally:
        s.close()
