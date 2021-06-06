import os
from typing import Optional, Awaitable

from tornado import web, template

from utils.utils import get_url, hash_string


def get_version():
    res = os.popen("git log -n1 --format=format:'%H'")
    return res.read()


def get_file_hashes():
    res = os.popen("git ls-files | xargs sha256sum")
    return res.read()


class Version(web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    async def get(self):
        file_hashes = get_file_hashes()

        loader = template.Loader("")
        html = loader.load(name="version/index.html")
        self.add_header("Content-Type", "text/html; charset=UTF-8")
        self.write(html.generate(version=get_version(),
                                 file_hashes=file_hashes,
                                 hash_of_file_hashes=hash_string(file_hashes),
                                 url=get_url(self)))
