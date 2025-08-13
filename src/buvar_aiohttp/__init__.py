import functools
import logging
import socket
import typing as t
from dataclasses import dataclass
from ssl import SSLContext

import aiohttp.web
import attr
import uritools
from buvar import config, context, di, fork, plugin, util

__version__ = "0.4.5"
__version_info__ = tuple(__version__.split("."))


@dataclass
class AioHttpConfig(config.Config, section="aiohttp"):
    host: str | None = None
    port: int | None = None
    path: str | None = None
    sock: socket.socket | None = None
    shutdown_timeout: float = 60.0
    ssl_context: SSLContext | None = None
    backlog: int = 128
    handle_signals: bool = False
    access_log: logging.Logger | None = util.resolve_dotted_name(
        "aiohttp.log:access_logger"
    )

    def __attrs_post_init__(self):
        # override with shared sockets
        aiohttp_sock = None

        if self.host or self.port:
            aiohttp_uri = uritools.uricompose(
                "tcp",
                self.host or "0.0.0.0",
                port=self.port or None,
            )
            aiohttp_sock = context.get(fork.Socket, name=str(aiohttp_uri), default=None)

        elif self.path:
            aiohttp_uri = uritools.uricompose("unix", path=self.path)
            aiohttp_sock = context.get(fork.Socket, name=str(aiohttp_uri), default=None)

        if aiohttp_sock:
            self.sock = aiohttp_sock
            self.host = None
            self.port = None

    async def site(self, runner: aiohttp.web.AppRunner):
        if self.host or self.port:
            return aiohttp.web.TCPSite(
                runner,
                host=self.host,
                port=self.port,
                backlog=self.backlog,
                shutdown_timeout=self.shutdown_timeout,
                ssl_context=self.ssl_context,
            )
        if self.path:
            return aiohttp.web.UnixSite(
                runner,
                path=self.path,
                backlog=self.backlog,
                shutdown_timeout=self.shutdown_timeout,
                ssl_context=self.ssl_context,
            )

        if self.sock:
            return aiohttp.web.SockSite(
                runner,
                sock=self.sock,
                backlog=self.backlog,
                shutdown_timeout=self.shutdown_timeout,
                ssl_context=self.ssl_context,
            )

        raise ValueError(
            f"You have to set a specific host/port, sock, path: {self}", self
        )

    async def run(self, app: aiohttp.web.Application):
        runner = context.add(
            aiohttp.web.AppRunner(
                app,
                access_log=self.access_log,
                handle_signals=self.handle_signals,
            )
        )
        await runner.setup()
        try:
            config = await di.nject(AioHttpConfig)
            site = await config.site(runner)

            cancel = context.get(plugin.Cancel)

            await site.start()
            await cancel.wait()
        finally:
            await runner.cleanup()


@functools.partial(config.relaxed_converter.register_structure_hook, socket.socket)
def _structure_socket(d, t):
    # try parsing a FD number first
    try:
        fd_num = int(d)
    except ValueError:
        pass
    else:
        import socket

        fd_sock = socket.fromfd(fd_num, socket.AF_UNIX, socket.SOCK_STREAM)
        return fd_sock
    raise ValueError(f"Socket string `{d}` not implemented", d)


@functools.partial(config.relaxed_converter.register_structure_hook, logging.Logger)
def _structure_logger(d, t):
    if isinstance(d, t):
        return d
    elif isinstance(d, str):
        return util.resolve_dotted_name(d)
    return d


@aiohttp.web.middleware
async def buvar_context_push_middleware(request, handler):
    """Push the stack of components for each request."""
    context.buvar_context.set(context.push())
    resp = await handler(request)
    return resp


async def prepare_app():
    context.add(
        aiohttp.web.Application(
            middlewares=[
                buvar_context_push_middleware,
                aiohttp.web.normalize_path_middleware(),
            ]
        )
    )


async def prepare_client_session(teardown: plugin.Teardown):
    aiohttp_client_session = context.add(aiohttp.client.ClientSession())

    teardown.add(aiohttp_client_session.close())


async def prepare_server(load: plugin.Loader):
    await load(prepare_app)
    aiohttp_app = context.get(aiohttp.web.Application)
    aiohttp_config = await di.nject(AioHttpConfig)
    yield aiohttp_config.run(aiohttp_app)


async def prepare(load: plugin.Loader):
    await load("buvar.config")
    await load(prepare_client_session)
    await load(prepare_server)
