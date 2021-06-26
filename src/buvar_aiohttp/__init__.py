import functools
import logging
import socket
import typing

import aiohttp.web
import attr
import uritools
from buvar import config, context, di, fork, plugin, util

try:
    from ssl import SSLContext
except ImportError:  # pragma: no cover
    SSLContext = typing.Any  # type: ignore

__version__ = "0.4.1"
__version_info__ = tuple(__version__.split("."))


@attr.s(auto_attribs=True)
class AioHttpConfig(config.Config, section="aiohttp"):
    host: typing.Optional[str] = None
    port: typing.Optional[int] = None
    path: typing.Optional[str] = None
    sock: typing.Optional[socket.socket] = None
    shutdown_timeout: float = 60.0
    ssl_context: typing.Optional[SSLContext] = None
    backlog: int = 128
    handle_signals: bool = False
    access_log: typing.Optional[logging.Logger] = util.resolve_dotted_name(
        "aiohttp.log:access_logger"
    )


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


async def prepare_app():
    context.add(
        aiohttp.web.Application(middlewares=[aiohttp.web.normalize_path_middleware()])
    )


async def prepare_client_session(teardown: plugin.Teardown):
    aiohttp_client_session = context.add(aiohttp.client.ClientSession())

    teardown.add(aiohttp_client_session.close())


def override_aiohttp_config(aiohttp_config: AioHttpConfig):
    aiohttp_sock = None

    if aiohttp_config.host or aiohttp_config.port:
        aiohttp_uri = uritools.uricompose(
            "tcp", aiohttp_config.host or "0.0.0.0", port=aiohttp_config.port or None
        )
        aiohttp_sock = context.get(fork.Socket, name=str(aiohttp_uri))

    elif aiohttp_config.path:
        aiohttp_uri = uritools.uricompose("unix", path=aiohttp_config.path)
        aiohttp_sock = context.get(fork.Socket, name=str(aiohttp_uri))

    if aiohttp_sock:
        aiohttp_config.sock = aiohttp_sock
        aiohttp_config.host = None
        aiohttp_config.port = None

    # cache this config
    context.add(aiohttp_config)


async def prepare_server(load: plugin.Loader):
    await load(prepare_app)
    aiohttp_app = context.get(aiohttp.web.Application)

    aiohttp_config = await di.nject(AioHttpConfig)

    # override if buvar provides socket already
    override_aiohttp_config(aiohttp_config)

    yield aiohttp.web._run_app(  # noqa: W0212
        aiohttp_app, **attr.asdict(aiohttp_config), print=None
    )


async def prepare(load: plugin.Loader):
    await load("buvar.config")
    await load(prepare_client_session)
    await load(prepare_server)
