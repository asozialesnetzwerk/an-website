import os

from utils.utils import get_url, hash_string, RequestHandlerCustomError

VERSION = os.popen("git log -n1 --format=format:'%H'").read()
FILE_HASHES = os.popen("git ls-files | xargs sha1sum").read()
HASH_OF_FILE_HASHES = hash_string(FILE_HASHES)
GH_PAGES_COMMIT_HASH = os.popen("git log -n1 --format=format:'%H' origin/gh-pages").read()


class Version(RequestHandlerCustomError):
    async def get(self):
        self.add_header("Content-Type", "text/html; charset=UTF-8")
        await self.render("pages/version.html",
                          version=VERSION,
                          file_hashes=FILE_HASHES,
                          hash_of_file_hashes=HASH_OF_FILE_HASHES,
                          gh_pages_commit_hash=GH_PAGES_COMMIT_HASH,
                          url=get_url(self)
                         )
