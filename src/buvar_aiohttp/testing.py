import pytest


@pytest.fixture
def buvar_aiohttp_app(buvar_plugin_context, buvar_stage):
    import aiohttp.web

    buvar_stage.load("buvar_aiohttp")

    app = buvar_plugin_context.get(aiohttp.web.Application)
    return app


@pytest.fixture
def buvar_aiohttp_client(
    buvar_aiohttp_app,
    aiohttp_client,
    buvar_plugin_context,
):
    import asyncio

    from buvar import testing

    client_coro = aiohttp_client(
        buvar_aiohttp_app,
    )

    def run():
        return asyncio.get_event_loop().run_until_complete(client_coro)

    client = testing.wrap_in_buvar_plugin_context(buvar_plugin_context, run)()
    return client
