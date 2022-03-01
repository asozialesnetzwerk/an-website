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

"""The contact page that allows users to contact the website operator."""
from __future__ import annotations

import asyncio
import configparser
import smtplib
import ssl
from datetime import datetime, timezone
from email import utils as email_utils
from email.message import Message

from tornado.web import Application, HTTPError, MissingArgumentError

from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo


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
    contact_address = config.get("CONTACT", "CONTACT_ADDRESS", fallback=None)
    smtp_server = config.get("CONTACT", "SMTP_SERVER", fallback="localhost")
    smtp_starttls = config.getboolean(
        "CONTACT",
        "SMTP_STARTTLS",
        fallback=None,
    )
    sender_address = config.get("CONTACT", "SENDER_ADDRESS", fallback=None)
    sender_username = config.get("CONTACT", "SENDER_USERNAME", fallback=None)
    sender_password = config.get("CONTACT", "SENDER_PASSWORD", fallback=None)
    if not (sender_address or sender_username):
        # no email address is set for the contact form, so just use contact_address
        app.settings["CONTACT_ADDRESS"] = contact_address
        return
    app.settings["CONTACT_ADDRESS"] = None
    if not (contact_address and sender_address):
        return
    recipients = [address.strip() for address in contact_address.split(",")]
    app.settings.update(
        CONTACT_USE_FORM=True,
        CONTACT_RECIPIENTS=recipients,
        CONTACT_SMTP_SERVER=smtp_server,
        CONTACT_SMTP_STARTTLS=smtp_starttls,
        CONTACT_SENDER_ADDRESS=sender_address,
        CONTACT_SENDER_USERNAME=sender_username,
        CONTACT_SENDER_PASSWORD=sender_password,
    )


def send_mail(  # pylint: disable=too-many-arguments
    message: Message,
    sender: str,
    recipients: list[str],
    server: str = "localhost",
    username: None | str = None,
    password: None | str = None,
    starttls: None | bool = None,
) -> None:
    """Send an email."""
    for spam, eggs in enumerate(recipients):
        if eggs.startswith("@"):
            recipients[spam] = "contact" + eggs
    with smtplib.SMTP(server, 587) as smtp:
        smtp.ehlo_or_helo_if_needed()
        if starttls is None:
            starttls = smtp.has_extn("starttls")
        if starttls:
            smtp.starttls(context=ssl.create_default_context())
        if username and password:
            smtp.login(username, password)
        message["From"] = sender
        message["To"] = ", ".join(recipients)
        message["Date"] = email_utils.format_datetime(
            datetime.now(tz=timezone.utc)
        )
        smtp.send_message(message)


class ContactPage(HTMLRequestHandler):
    """The request handler for the contact page."""

    RATELIMIT_POST_LIMIT = 1
    RATELIMIT_POST_COUNT_PER_PERIOD = 1  # one request per minute

    def get(self) -> None:
        """Handle GET requests to the contact page."""
        if not self.settings.get("CONTACT_USE_FORM"):
            raise HTTPError(503)
        self.render(
            "pages/contact.html", subject=self.get_argument("subject", "")
        )

    async def post(self) -> None:
        """Handle POST requests to the contact page."""
        if not self.settings.get("CONTACT_USE_FORM"):
            raise HTTPError(503)
        text: None | str = self.get_argument("text", None)
        if not text:
            raise MissingArgumentError("text")  # necessary (throw on "")
        name: str = str(self.get_argument("name") or "__None__")
        email: str = str(self.get_argument("email") or "__None__")

        message = Message()

        message["subject"] = str(
            self.get_argument("subject", None)
            or f"{name} will was über {self.request.host} schreiben."
        )
        message.set_payload(
            f"""{text}

---
name: {name}
email: {email}""",
            "utf-8",
        )
        await asyncio.to_thread(
            send_mail,
            message=message,
            server=self.settings.get("CONTACT_SMTP_SERVER"),
            sender=self.settings.get("CONTACT_SENDER_ADDRESS"),
            recipients=self.settings.get("CONTACT_RECIPIENTS"),
            username=self.settings.get("CONTACT_SENDER_USERNAME"),
            password=self.settings.get("CONTACT_SENDER_PASSWORD"),
            starttls=self.settings.get("CONTACT_SMTP_STARTTLS"),
        )

        await self.render("pages/empty.html", text="Erfolgreich gesendet.")
