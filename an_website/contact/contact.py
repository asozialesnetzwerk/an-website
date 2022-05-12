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

"""A page that allows users to contact the website operator."""

from __future__ import annotations

import asyncio
import configparser
import logging
import smtplib
import ssl
import sys
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from email import utils as email_utils
from email.message import Message
from math import pi
from typing import Any, cast
from urllib.parse import quote, urlencode

from tornado.web import Application, HTTPError, MissingArgumentError

from .. import NAME
from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/kontakt", ContactPage),),
        name="Kontakt-Formular",
        description="Nehme mit dem Betreiber der Webseite Kontakt auf.",
        path="/kontakt",
        keywords=("Kontakt", "Formular"),
        aliases=("/contact",),
        hidden=True,
    )


def apply_contact_stuff_to_app(
    app: Application, config: configparser.ConfigParser
) -> None:
    """Apply contact stuff to the app."""
    contact_address = config.get(
        "CONTACT",
        "CONTACT_ADDRESS",
        fallback=f"{NAME.removesuffix('-dev')}@restmail.net"
        if app.settings.get("debug")
        else "",
    )
    sender_address = config.get(
        "CONTACT",
        "SENDER_ADDRESS",
        fallback="Marcell D'Avis <davis@1und1.de>"
        if contact_address.endswith("@restmail.net")
        else None,
    )

    if not sender_address:
        # the contact form in other mode if no sender address is set
        app.settings.update(
            CONTACT_ADDRESS=contact_address,
            CONTACT_USE_FORM=1,
        )
        return
    app.settings["CONTACT_ADDRESS"] = None

    if not (contact_address and sender_address):
        return

    app.settings.update(
        CONTACT_USE_FORM=2,
        CONTACT_RECIPIENTS={
            address.strip() for address in contact_address.split(",")
        },
        CONTACT_SMTP_SERVER=config.get(
            "CONTACT",
            "SMTP_SERVER",
            fallback="restmail.net"
            if contact_address.endswith("@restmail.net")
            else "localhost",
        ),
        CONTACT_SMTP_PORT=config.getint(
            "CONTACT",
            "SMTP_PORT",
            fallback=25 if contact_address.endswith("@restmail.net") else 587,
        ),
        CONTACT_SMTP_STARTTLS=config.getboolean(
            "CONTACT",
            "SMTP_STARTTLS",
            fallback=None,
        ),
        CONTACT_SENDER_ADDRESS=sender_address,
        CONTACT_SENDER_USERNAME=config.get(
            "CONTACT", "SENDER_USERNAME", fallback=None
        ),
        CONTACT_SENDER_PASSWORD=config.get(
            "CONTACT", "SENDER_PASSWORD", fallback=None
        ),
    )


def send_message(  # pylint: disable=too-many-arguments
    message: Message,
    from_address: str,
    recipients: Iterable[str],
    server: str = "localhost",
    sender: None | str = None,
    username: None | str = None,
    password: None | str = None,
    starttls: None | bool = None,
    port: int = 587,
    *,
    date: None | datetime = None,
) -> dict[str, tuple[int, bytes]]:
    """Send an email."""
    recipients = list(recipients)
    for spam, eggs in enumerate(recipients):
        if eggs.startswith("@"):
            recipients[spam] = "contact" + eggs

    message["Date"] = email_utils.format_datetime(
        date or datetime.now(tz=timezone.utc)
    )

    if sender:
        message["Sender"] = sender
    message["From"] = from_address
    message["To"] = ", ".join(recipients)

    with smtplib.SMTP(server, port) as smtp:
        smtp.set_debuglevel(sys.flags.dev_mode * 2)
        smtp.ehlo_or_helo_if_needed()
        if starttls is None:
            starttls = smtp.has_extn("starttls")
        if starttls:
            smtp.starttls(context=ssl.create_default_context())
        if username and password:
            smtp.login(username, password)
        return smtp.send_message(message)


def add_geoip_info_to_message(
    message: Message,
    geoip_info: dict[str, Any],
    header_prefix: str = "X-GeoIP",
) -> None:
    """Add GeoIP information to the message."""
    for spam, eggs in geoip_info.items():
        header = f"{header_prefix}-{spam.replace('_', '-')}"
        if isinstance(eggs, dict):
            add_geoip_info_to_message(message, eggs, header)
        else:
            message[header] = str(eggs)


class ContactPage(HTMLRequestHandler):
    """The request handler for the contact page."""

    RATELIMIT_POST_LIMIT = 5
    RATELIMIT_POST_COUNT_PER_PERIOD = 1
    RATELIMIT_POST_PERIOD = 120

    ACCESS_LOG: dict[str, float] = {}

    def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the contact page."""
        if not self.settings.get("CONTACT_USE_FORM"):
            raise HTTPError(503)
        if head:
            return

        curr_time = time.monotonic()

        # clean up old items from the access log
        for key, value in tuple(self.ACCESS_LOG.items()):
            if curr_time - value > 10:
                del self.ACCESS_LOG[key]

        self.ACCESS_LOG[str(self.request.remote_ip)] = curr_time

        self.render(
            "pages/contact.html",
            subject=self.get_argument("subject", ""),
            message=self.get_argument("message", ""),
        )

    async def post(self) -> None:
        """Handle POST requests to the contact page."""
        if not self.settings.get("CONTACT_USE_FORM"):
            raise HTTPError(503)

        if atime := self.ACCESS_LOG.get(cast(str, self.request.remote_ip)):
            del self.ACCESS_LOG[cast(str, self.request.remote_ip)]
            if time.monotonic() - atime < pi:
                logger.info("Rejected message because of timing")
                await self.render(
                    "pages/empty.html",
                    text="Nicht gesendet, da du zu schnell warst.",
                )
                return

        text = self.get_argument("nachricht")
        if not text:
            raise MissingArgumentError("nachricht")  # raise on empty message

        name = self.get_argument("name", "")
        address = self.get_argument("addresse", "")
        from_address = (
            f"{name} <{address or 'anonymous@foo.bar'}>"
            if name
            else address or "anonymous@foo.bar"
        )

        message = Message()

        message["Subject"] = str(
            self.get_argument("subjekt", "")
            or f"{name or address or 'Jemand'} "
            f"will etwas über {self.request.host_name} schreiben."
        )
        message.set_payload(text, "utf-8")
        if honeypot := self.get_argument("message", ""):  # 🍯
            logger.info(
                "rejected message: %s",
                {
                    "Subject": message["Subject"],
                    "message": message,
                    "from_address": from_address,
                    "geoip": await self.geoip(),
                    "🍯": honeypot,
                },
            )
            await self.render("pages/empty.html", text="Erfolgreich gesendet.")
            return

        if self.settings.get("CONTACT_USE_FORM") == 1:
            query = urlencode(
                {
                    "subject": message["Subject"],
                    "body": f"{text}\n\nVon: {from_address}",
                },
                quote_via=quote,
            )
            self.redirect(
                f"mailto:{self.settings.get('CONTACT_ADDRESS')}?{query}"
            )
            return

        geoip = await self.geoip()
        if geoip:
            add_geoip_info_to_message(message, geoip)

        await asyncio.to_thread(
            send_message,
            message=message,
            from_address=from_address,
            server=self.settings.get("CONTACT_SMTP_SERVER"),  # type: ignore[arg-type]
            sender=self.settings.get("CONTACT_SENDER_ADDRESS"),
            recipients=self.settings.get("CONTACT_RECIPIENTS"),  # type: ignore
            username=self.settings.get("CONTACT_SENDER_USERNAME"),
            password=self.settings.get("CONTACT_SENDER_PASSWORD"),
            starttls=self.settings.get("CONTACT_SMTP_STARTTLS"),
            port=self.settings.get("CONTACT_SMTP_PORT"),  # type: ignore[arg-type]
            date=await self.get_time(),
        )

        await self.render("pages/empty.html", text="Erfolgreich gesendet.")
