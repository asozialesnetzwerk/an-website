# pylint: disable=subprocess-run-check


import hashlib
import subprocess

from .. import DIR
from ..utils.utils import BaseRequestHandler, ModuleInfo

VERSION = subprocess.run(
    "git rev-parse HEAD", cwd=DIR, shell=True, capture_output=True, text=True
).stdout
FILE_HASHES = subprocess.run(
    "git ls-files | xargs sha1sum",
    cwd=DIR,
    shell=True,
    capture_output=True,
    text=True,
).stdout
HASH_OF_FILE_HASHES = hashlib.sha1(FILE_HASHES.encode("utf-8")).hexdigest()
GH_PAGES_COMMIT_HASH = subprocess.run(
    "git rev-parse origin/gh-pages",
    cwd=DIR,
    shell=True,
    capture_output=True,
    text=True,
).stdout


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=((r"/version/?", Version),),
        name="Versions-Informationen",
        description="Die aktuelle Version der Webseite",
        path="/version",
    )


class Version(BaseRequestHandler):
    async def get(self):
        await self.render(
            "pages/version.html",
            version=VERSION,
            file_hashes=FILE_HASHES,
            hash_of_file_hashes=HASH_OF_FILE_HASHES,
            gh_pages_commit_hash=GH_PAGES_COMMIT_HASH,
        )
