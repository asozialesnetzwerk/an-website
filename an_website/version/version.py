import hashlib

from ..utils.utils import RequestHandlerCustomError, run_shell_command

VERSION = run_shell_command("cd an_website && git log -n1 --format=format:'%H'")
FILE_HASHES = run_shell_command("cd an_website && git ls-files | xargs sha1sum")
HASH_OF_FILE_HASHES = hashlib.sha1(FILE_HASHES.encode("utf-8")).hexdigest()
GH_PAGES_COMMIT_HASH = run_shell_command("cd an_website && git log -n1 --format=format:'%H' origin/gh-pages")


class Version(RequestHandlerCustomError):
    async def get(self):
        await self.render("pages/version.html",
                          version=VERSION,
                          file_hashes=FILE_HASHES,
                          hash_of_file_hashes=HASH_OF_FILE_HASHES,
                          gh_pages_commit_hash=GH_PAGES_COMMIT_HASH
                          )
