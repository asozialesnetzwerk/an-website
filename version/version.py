import os

from utils.utils import get_url, hash_string, RequestHandlerCustomError

VERSION = os.popen("git log -n1 --format=format:'%H'").read()
GH_PAGES_COMMIT_HASH = os.popen("git log -n1 --format=format:'%H' origin/gh-pages").read()
FILE_HASHES = os.popen("git ls-files | xargs sha256sum").read()


class Version(RequestHandlerCustomError):
    async def get(self):
        self.add_header("Content-Type", "text/html; charset=UTF-8")
        await self.render("pages/version.html", version=VERSION,
                          file_hashes=FILE_HASHES,
                          hash_of_file_hashes=hash_string(FILE_HASHES),
                          gh_pages_commit_hash=GH_PAGES_COMMIT_HASH,
                          url=get_url(self))
