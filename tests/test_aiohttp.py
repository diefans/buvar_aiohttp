import socket

import pytest


# running in manylinux docker
# the loop fixture in buvar.testing seem to have no effect
@pytest.fixture
def loop(event_loop):
    return event_loop


@pytest.mark.asyncio
@pytest.mark.buvar_plugins("buvar.config")
async def test_app_dummy(buvar_aiohttp_app, aiohttp_client, caplog):
    import logging

    import aiohttp.web

    async def hello(request):
        return aiohttp.web.Response(body=b"Hello, world")

    buvar_aiohttp_app.router.add_route("GET", "/", hello)

    caplog.set_level(logging.DEBUG)
    client = await aiohttp_client(buvar_aiohttp_app)
    resp = await client.get("/")
    assert "Hello, world" == await resp.text()
    assert caplog.messages


@pytest.mark.asyncio
@pytest.mark.buvar_plugins("buvar.config")
async def test_app_request_context_pushed(buvar_aiohttp_app, aiohttp_client, caplog):
    import logging
    from dataclasses import dataclass

    import aiohttp.web
    from buvar import di

    @dataclass
    class Foo:
        data: str = "default"

    @aiohttp.web.middleware
    async def test_middleware_prepare_request_context(request, handler):
        from buvar import context

        if test_data := request.headers.get("X-Test-Data"):
            context.add(Foo(test_data))
        else:
            context.add(await di.nject(Foo))

        resp = await handler(request)
        return resp

    async def hello(_):
        foo = await di.nject(Foo)
        return aiohttp.web.Response(body=f"Hello, world - {foo.data}".encode())

    buvar_aiohttp_app.middlewares.append(test_middleware_prepare_request_context)
    buvar_aiohttp_app.router.add_route("GET", "/", hello)
    di.register(Foo)

    caplog.set_level(logging.DEBUG)
    client = await aiohttp_client(buvar_aiohttp_app)

    resp = await client.get("/", headers={"X-Test-Data": "foobar"})
    assert await resp.text() == "Hello, world - foobar"

    resp = await client.get("/")
    assert await resp.text() == "Hello, world - default", "Context is not pushed"

    assert caplog.messages


def test_structure_config():
    import socket

    import buvar_aiohttp

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        source = {"sock": s.fileno()}
        config = buvar_aiohttp.config.relaxed_converter.structure(
            source, buvar_aiohttp.AioHttpConfig
        )
        assert isinstance(config.sock, socket.socket)
        config.sock.close()


@pytest.mark.asyncio
@pytest.mark.buvar_plugins("tests.minimal_app")
async def test_run_minimal_app(buvar_aiohttp_client, caplog):
    import logging

    caplog.set_level(logging.DEBUG)
    resp = await buvar_aiohttp_client.get("/")
    assert "Hello, world" == await resp.text()
    assert caplog.messages


@pytest.mark.asyncio
@pytest.mark.buvar_plugins("buvar_aiohttp")
@pytest.mark.parametrize(
    "settings, site_cls",
    [
        ({"port": 12345}, "TCPSite"),
        ({"host": "0.0.0.0"}, "TCPSite"),
        ({"path": "/tmp/foo.sock"}, "UnixSite"),
        (
            {"sock": socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)},
            "SockSite",
        ),
        ({}, ValueError),
    ],
)
async def test_sites(settings, site_cls):
    import aiohttp.web
    from buvar import di

    import buvar_aiohttp

    config = buvar_aiohttp.AioHttpConfig(**settings)

    app = await di.nject(aiohttp.web.Application)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    if type(site_cls) is type and issubclass(site_cls, Exception):
        with pytest.raises(site_cls):
            await config.site(runner)
    else:
        site = await config.site(runner)
        assert type(site).__name__ == site_cls
