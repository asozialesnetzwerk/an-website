# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Website of the AN. Loads config and modules and starts tornado."""
from __future__ import annotations

import asyncio
import configparser
import importlib
import logging
import os
import ssl
import sys
from typing import Optional

import aioredis  # type: ignore
import ecs_logging
from elasticapm.contrib.tornado import ElasticAPM  # type: ignore
from elasticsearch import AsyncElasticsearch
from tornado.httpclient import AsyncHTTPClient
from tornado.log import LogFormatter
from tornado.web import Application, RedirectHandler

from . import DIR, patches
from .utils.request_handler import BaseRequestHandler, NotFound
from .utils.utils import (
    Handler,
    HandlerTuple,
    ModuleInfo,
    Timer,
    time_function,
)
from .version import version

# list of blocked modules
IGNORED_MODULES = [
    "patches.*",
    "static.*",
    "templates.*",
    "utils.utils",
    "swapped_words.sw_config_file",
]

logger = logging.getLogger(__name__)


# add all the information from the packages to a list
# this calls the get_module_info function in every file
# files/dirs starting with '_' gets ignored
def get_module_infos() -> tuple[ModuleInfo, ...]:
    """Import the modules and return the loaded module infos in a tuple."""
    module_infos: list[ModuleInfo] = []
    loaded_modules: list[str] = []
    errors: list[str] = []

    for potential_module in os.listdir(DIR):
        if (
            potential_module.startswith("_")
            or f"{potential_module}.*" in IGNORED_MODULES
            or not os.path.isdir(f"{DIR}/{potential_module}")
        ):
            continue

        for potential_file in os.listdir(f"{DIR}/{potential_module}"):
            module_name = f"{potential_module}.{potential_file[:-3]}"
            if (
                not potential_file.endswith(".py")
                or module_name in IGNORED_MODULES
                or potential_file.startswith("_")
            ):
                continue

            import_timer = Timer()
            module = importlib.import_module(
                f".{module_name}",
                package="an_website",
            )
            if "get_module_info" not in dir(module):
                errors.append(
                    f"{DIR}/{potential_module}/{potential_file} has no "
                    f"'get_module_info' method. Please add the method or add "
                    f"'{potential_module}.*' or '{module_name}' to "
                    f"IGNORED_MODULES."
                )
                continue

            if (
                (  # check if the annotations specify the return
                    # type as Module info
                    module.get_module_info.__annotations__.get(  # type: ignore
                        "return", ""
                    )
                    == "ModuleInfo"
                )
                # check if returned module_info is type ModuleInfo
                and isinstance(
                    module_info := module.get_module_info(),  # type: ignore
                    ModuleInfo,
                )
            ):
                module_infos.append(module_info)
                loaded_modules.append(module_name)

                if import_timer.stop() > 0.1:
                    logger.warning(
                        "Import of %s took %ss that's affecting the startup "
                        "time.",
                        module_name,
                        import_timer.execution_time,
                    )
                continue

            errors.append(
                f"'get_module_info' in {DIR}/{potential_module}"
                f"/{potential_file} does not return ModuleInfo. "
                f"Please add/fix the return type or add "
                f"'{potential_module}.*' or '{module_name}' to "
                f"IGNORED_MODULES."
            )

    if len(errors) > 0:
        if sys.flags.dev_mode:
            # exit to make sure it gets fixed:
            sys.exit("\n".join(errors))
        else:
            # don't exit in production to keep stuff running:
            logger.error("\n".join(errors))

    logger.info(
        "loaded %d modules: '%s'",
        len(loaded_modules),
        "', '".join(loaded_modules),
    )
    logger.info(
        "ignored %d modules: '%s'",
        len(IGNORED_MODULES),
        "', '".join(IGNORED_MODULES),
    )

    sort_module_infos(module_infos)

    # make module_infos immutable so it never changes:
    return tuple(module_infos)


def sort_module_infos(module_infos: list[ModuleInfo]):
    """Sort a list of module info and move the main page to the top."""
    # sort it so the order makes sense.
    module_infos.sort()

    # move the main page to the top:
    for _i, info in enumerate(module_infos):
        if info.path == "/":
            module_infos.insert(0, module_infos.pop(_i))
            break


def get_all_handlers(
    module_infos: tuple[ModuleInfo, ...],
) -> HandlerTuple:
    """
    Parse the module information and return the handlers in a tuple.

    If a handler has only 2 elements a dict with title and description gets
    added. This information is gotten from the module info.
    """
    handlers: list[Handler] = []

    for module_info in module_infos:
        for handler in module_info.handlers:
            # if the handler is a request handler from us
            # and not a built-in like StaticFileHandler
            if issubclass(handler[1], BaseRequestHandler):
                if len(handler) == 2:
                    # if dict as third arg is needed
                    # "title" and "description" have to be specified
                    # otherwise the info is taken from the module info
                    handler = (
                        handler[0],
                        handler[1],
                        {
                            "title": module_info.name,
                            "description": module_info.description,
                        },
                    )
                if len(handler) >= 3:
                    # mypy doesn't like this
                    _args_dict = handler[2]  # type: ignore
                    _args_dict["module_info"] = module_info
            handlers.append(handler)
        if module_info.path is not None and module_info.aliases is not None:
            for alias in module_info.aliases:
                handlers.append(
                    (
                        # (.*) -> add group that matches anything
                        alias + "(.*)",
                        RedirectHandler,
                        # {0} -> the part after the alias (.*)
                        {"url": module_info.path + "{0}"},
                    )
                )

    return tuple(handlers)


def make_app() -> Application:
    """Create the tornado application and return it."""
    module_infos, duration = time_function(get_module_infos)
    if duration > 1:
        logger.warning(
            "Getting the module infos took %ss. That's probably too long.",
            duration,
        )
    return Application(
        get_all_handlers(module_infos),  # type: ignore
        MODULE_INFOS=module_infos,
        # General settings
        autoreload=False,
        compress_response=True,
        debug=bool(sys.flags.dev_mode),
        default_handler_class=NotFound,
        websocket_ping_interval=10,
        # Template settings
        template_path=f"{DIR}/templates",
        # Static file settings
        static_path=f"{DIR}/static",
    )


def apply_config_to_app(app: Application, config: configparser.ConfigParser):
    """Apply the config (from the config.ini file) to the application."""
    app.settings["CONFIG"] = config

    app.settings["TRUSTED_API_SECRETS"] = tuple(
        secret.strip()
        for secret in config.get(
            "GENERAL", "TRUSTED_API_SECRETS", fallback="an-website"
        ).split(",")
    )

    app.settings["LINK_TO_HTTPS"] = config.getboolean(
        "GENERAL", "LINK_TO_HTTPS", fallback=False
    )

    # used in the header template
    app.settings["CONTACT_EMAIL"] = config.get(
        "GENERAL", "CONTACT_EMAIL", fallback=None
    )
    # whether ratelimits are enabled
    app.settings["ratelimits"] = config.getboolean(
        "GENERAL", "RATELIMITS", fallback=True
    )

    app.settings["ELASTIC_APM"] = {
        "ENABLED": config.getboolean("ELASTIC_APM", "ENABLED", fallback=False),
        "SERVER_URL": config.get(
            "ELASTIC_APM", "SERVER_URL", fallback="http://localhost:8200"
        ),
        "SECRET_TOKEN": config.get(
            "ELASTIC_APM", "SECRET_TOKEN", fallback=None
        ),
        "API_KEY": config.get("ELASTIC_APM", "API_KEY", fallback=None),
        "SERVICE_NAME": "an-website",
        "SERVICE_VERSION": version.VERSION.strip(),
        "ENVIRONMENT": "production"
        if not sys.flags.dev_mode
        else "development",
        "DEBUG": True,
        "CAPTURE_BODY": "errors",
    }
    app.settings["ELASTIC_APM_AGENT"] = ElasticAPM(app)
    app.settings["ELASTICSEARCH"] = AsyncElasticsearch(
        cloud_id=config.get("ELASTICSEARCH", "CLOUD_ID", fallback=None),
        host=config.get("ELASTICSEARCH", "HOST", fallback="localhost"),
        port=config.get("ELASTICSEARCH", "PORT", fallback=None),
        url_prefix=config.get("ELASTICSEARCH", "URL_PREFIX", fallback=None),
        use_ssl=config.get("ELASTICSEARCH", "USE_SSL", fallback=False),
        verify_certs=config.getboolean(
            "ELASTICSEARCH", "VERIFY_CERTS", fallback=True
        ),
        http_auth=(
            config.get("ELASTICSEARCH", "USERNAME"),
            config.get("ELASTICSEARCH", "PASSWORD"),
        )
        if config.get("ELASTICSEARCH", "USERNAME", fallback=None)
        and config.get("ELASTICSEARCH", "PASSWORD", fallback=None)
        else None,
        api_key=config.get("ELASTICSEARCH", "API_KEY", fallback=None),
        client_cert=config.get("ELASTICSEARCH", "CLIENT_CERT", fallback=None),
        client_key=config.get("ELASTICSEARCH", "CLIENT_KEY", fallback=None),
        retry_on_timeout=config.get(
            "ELASTICSEARCH", "RETRY_ON_TIMEOUT", fallback=False
        ),
        send_get_body_as=config.get(
            "ELASTICSEARCH", "SEND_GET_BODY_AS", fallback=None
        ),
        http_compress=True,
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60,
        headers={
            "accept": "application/vnd.elasticsearch+json; compatible-with=7"
        },
    )
    app.settings["ELASTICSEARCH_PREFIX"] = (
        config.get("ELASTICSEARCH", "PREFIX", fallback="an-website") + "-"
    )
    # sys.exit(
    #     asyncio.get_event_loop().run_until_complete(
    #         app.settings["ELASTICSEARCH"].info()
    #     )
    # )
    app.settings["REDIS"] = aioredis.Redis(
        connection_pool=aioredis.BlockingConnectionPool.from_url(
            config.get("REDIS", "URL", fallback="redis://localhost"),
            db=config.getint("REDIS", "DB", fallback=None),
            username=config.get("REDIS", "USERNAME", fallback=None),
            password=config.get("REDIS", "PASSWORD", fallback=None),
        )
    )
    app.settings["REDIS_PREFIX"] = (
        config.get("REDIS", "PREFIX", fallback="an-website") + ":"
    )
    # sys.exit(
    #     asyncio.get_event_loop()
    #     .run_until_complete(app.settings["REDIS"].execute_command("LOLWUT"))
    #     .decode("utf-8")
    # )


def get_ssl_context(
    config: configparser.ConfigParser,
) -> Optional[ssl.SSLContext]:
    """Create SSL config and configure using the config."""
    if config.getboolean("SSL", "ENABLED", fallback=False):
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            config.get("SSL", "CERTFILE"),
            config.get("SSL", "KEYFILE", fallback=None),
            config.get("SSL", "PASSWORD", fallback=None),
        )
        return ssl_ctx

    return None


def setup_logger():
    """Configure the root logger."""
    root_logger = logging.getLogger()
    root_logger.setLevel(
        logging.INFO if not sys.flags.dev_mode else logging.DEBUG
    )
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(
        LogFormatter() if not sys.flags.dev_mode else logging.Formatter()
    )

    root_logger.addHandler(stream_handler)

    if not sys.flags.dev_mode:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            "logs/an-website.log", "midnight", backupCount=7, utc=True
        )
        file_handler.setFormatter(ecs_logging.StdlibFormatter())
        root_logger.addHandler(file_handler)

    logging.captureWarnings(True)


def main():
    """
    Start everything.

    This is the main function that is called when running this file.
    """
    patches.apply()
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    config = configparser.ConfigParser(interpolation=None)
    config.read("config.ini")

    setup_logger()

    # read ignored modules from the config
    for module_name in config.get(
        "GENERAL", "IGNORED_MODULES", fallback=""
    ).split(","):
        module_name = module_name.strip()
        if len(module_name) > 0:
            IGNORED_MODULES.append(module_name)

    app = make_app()

    apply_config_to_app(app, config)

    app.listen(
        config.getint("TORNADO", "PORT", fallback=8080),
        protocol=config.get("TORNADO", "PROTOCOL", fallback=None),
        xheaders=config.getboolean("TORNADO", "BEHIND_PROXY", fallback=False),
        decompress_request=True,
        ssl_options=get_ssl_context(config),
    )

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
