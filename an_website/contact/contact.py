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

"""The contact page, that allows users to contact the website owner."""
from __future__ import annotations

import configparser
import smtplib
import ssl
import sys
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
        description="Nehme mit dem Besitzer der Webseite kontakt auf.",
        path="/kontakt",
        keywords=("Kontakt", "Formular"),
        aliases=("/contact",),
        hidden=True,
    )


def apply_contact_stuff_to_app(
    app: Application, config: configparser.ConfigParser
) -> None:
    """Apply contact stuff to the app."""
    contact_email = config.get("CONTACT", "CONTACT_EMAIL", fallback=None)
    sender_email_address = config.get(
        "CONTACT", "SENDER_EMAIL_ADDRESS", fallback=None
    )
    sender_account_name = config.get(
        "CONTACT", "SENDER_ACCOUNT_NAME", fallback=None
    )
    if not (sender_email_address or sender_account_name):
        app.settings["CONTACT_EMAIL"] = contact_email
        return  # no email for form is given, so just use contact_email
    app.settings["CONTACT_EMAIL"] = None

    if not (
        sender_email_address and sender_account_name
    ):  # only one of them is truthy
        # if one of them isn't present fallback to the other
        sender_email_address = sender_email_address or sender_account_name
        sender_account_name = sender_email_address

    receiver_address = contact_email or sender_email_address

    sender_smtp_server = config.get(
        "CONTACT", "SENDER_SMTP_SERVER", fallback=None
    )
    if not sender_smtp_server:
        if sys.flags.dev_mode:
            raise LookupError(
                "No SENDER_SMTP_SERVER in CONTACT section "
                "of config.ini given."
            )
        return

    sender_account_password = config.get(
        "CONTACT", "SENDER_ACCOUNT_PASSWORD", fallback=None
    )
    if not sender_smtp_server:
        if sys.flags.dev_mode:
            raise LookupError(
                "No SENDER_ACCOUNT_PASSWORD in CONTACT section "
                "of config.ini given."
            )
        return

    app.settings.update(
        CONTACT_USE_FORM=True,
        CONTACT_SENDER_EMAIL=sender_email_address,
        CONTACT_SENDER_ACCOUNT=sender_account_name,
        CONTACT_RECEIVER=receiver_address,
        CONTACT_ACC_PASSWORD=sender_account_password,
        CONTACT_SMTP_SERVER=sender_smtp_server,
        CONTACT_SMTP_TLS=config.getboolean(
            "CONTACT",
            "SENDER_SMTP_USE_TLS",
            fallback=True,
        ),
    )


def send_mail(  # pylint: disable=too-many-arguments
    message: Message,
    receiver_email: str,
    sender_account_name: str,
    sender_email: str,
    sender_password: str,
    smtp_server: str,
    use_tls: bool = True,
) -> None:
    """Send an email."""
    if receiver_email.startswith("@"):
        receiver_email = "contact" + receiver_email
    with smtplib.SMTP(smtp_server, 587 if use_tls else 25) as server:
        if use_tls:
            server.starttls(context=ssl.create_default_context())
        server.login(sender_account_name, sender_password)
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Date"] = email_utils.format_datetime(
            datetime.now(tz=timezone.utc)
        )
        server.send_message(
            message, from_addr=sender_email, to_addrs=receiver_email
        )


class ContactPage(HTMLRequestHandler):
    """The request handler for the contact page."""

    def get(self) -> None:
        """Handle get requests to the contact page."""
        if not self.settings.get("CONTACT_USE_FORM"):
            raise HTTPError(501)
        self.render("pages/contact.html")

    async def post(self) -> None:
        """Handle post requests to the contact page."""
        if not self.settings.get("CONTACT_USE_FORM"):
            raise HTTPError(501)
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
        send_mail(
            message=message,
            receiver_email=self.settings.get("CONTACT_RECEIVER"),  # type: ignore
            sender_account_name=self.settings.get(  # type: ignore
                "CONTACT_SENDER_ACCOUNT"
            ),
            sender_email=self.settings.get("CONTACT_SENDER_EMAIL"),  # type: ignore
            sender_password=self.settings.get("CONTACT_ACC_PASSWORD"),  # type: ignore
            smtp_server=self.settings.get("CONTACT_SMTP_SERVER"),  # type: ignore
            use_tls=self.settings.get("CONTACT_SMTP_TLS"),  # type: ignore
        )

        await self.render("pages/empty.html", text="Erfolgreich gesendet.")
