import hashlib

from ..utils.utils import RequestHandlerCustomError, run_shell

VERSION = await run_shell("cd an_website && git log -n1 --format=format:'%H'")[1].decode('utf-8')
FILE_HASHES = await run_shell("cd an_website && git ls-files | xargs sha1sum")[1].decode('utf-8')
HASH_OF_FILE_HASHES = hashlib.sha1(FILE_HASHES.encode("utf-8")).hexdigest()
GH_PAGES_COMMIT_HASH = await run_shell("cd an_website && git log -n1 --format=format:'%H' origin/gh-pages")[1].decode('utf-8') # pylint: disable=line-too-long


class Version(RequestHandlerCustomError):
    async def get(self):
        await self.render("pages/version.html",
                          version=VERSION,
                          file_hashes=FILE_HASHES,
                          hash_of_file_hashes=HASH_OF_FILE_HASHES,
                          gh_pages_commit_hash=GH_PAGES_COMMIT_HASH
                          )
