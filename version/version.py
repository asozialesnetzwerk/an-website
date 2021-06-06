from typing import Optional, Awaitable
import os

from tornado import web, template

from utils.utils import get_url, hash_string

VERSION = os.popen("git log -n1 --format=format:'%H'").read()
FILE_HASHES = os.popen("git ls-files | xargs sha256sum").read()


class Version(web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    async def get(self):
        loader = template.Loader("")
        html = loader.load(name="version/index.html")
        self.add_header("Content-Type", "text/html; charset=UTF-8")
        self.write(html.generate(version=VERSION,
                                 file_hashes=FILE_HASHES,
                                 hash_of_file_hashes=hash_string(FILE_HASHES),
                                 url=get_url(self)))
