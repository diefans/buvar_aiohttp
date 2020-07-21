import pytest


@pytest.fixture
def loop(event_loop):
    # use event loop from pytest-asyncio
    return event_loop


@pytest.fixture
def buvar_aiohttp_app(buvar_plugin_context, buvar_stage):
    import aiohttp.web

    buvar_stage.load("buvar_aiohttp")

    app = buvar_plugin_context.get(aiohttp.web.Application)
    return app
