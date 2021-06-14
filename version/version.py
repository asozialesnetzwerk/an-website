import os
import hashlib

from utils.utils import RequestHandlerCustomError, VERSION

FILE_HASHES = os.popen("git ls-files | xargs sha1sum").read()
HASH_OF_FILE_HASHES = hashlib.sha1(FILE_HASHES.encode("utf-8")).hexdigest()
GH_PAGES_COMMIT_HASH = os.popen("git log -n1 --format=format:'%H' origin/gh-pages").read()


class Version(RequestHandlerCustomError):
    async def get(self):
        await self.render("pages/version.html",
                          file_hashes=FILE_HASHES,
                          hash_of_file_hashes=HASH_OF_FILE_HASHES,
                          gh_pages_commit_hash=GH_PAGES_COMMIT_HASH
                          )
