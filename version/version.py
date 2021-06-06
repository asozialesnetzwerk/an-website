from typing import Optional, Awaitable

from tornado import web


def get_version():
    f = open("version/version.txt", "r")
    version = f.read()
    f.close()
    return version


class Version(web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get(self):
        self.write(get_version())
