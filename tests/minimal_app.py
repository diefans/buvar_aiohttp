import aiohttp.web
from buvar import context, di, fork, plugin

from buvar_aiohttp import AioHttpConfig


async def hello(request):
    return aiohttp.web.Response(body=b"Hello, world")


async def prepare(load: plugin.Loader):
    # provide config
    context.add(AioHttpConfig(host="0.0.0.0", port=5678))

    # prepare server site
    await load("buvar_aiohttp")

    # mount routes
    app = await di.nject(aiohttp.web.Application)
    app.router.add_route("GET", "/", hello)


if __name__ == "__main__":
    # start a process for each available CPU and provide a shared socket to all
    # children
    fork.stage(prepare, forks=0, sockets=["tcp://:5678"])
