import hashlib
import asyncio

from ..utils.utils import RequestHandlerCustomError, run_shell

loop = asyncio.get_event_loop()
VERSION = loop.create_task(run_shell("cd an_website && git log -n1 --format=format:'%H'"))
FILE_HASHES = loop.create_task(run_shell("cd an_website && git ls-files | xargs sha1sum"))
GH_PAGES_COMMIT_HASH = loop.create_task(
    run_shell("cd an_website && git log -n1 --format=format:'%H' origin/gh-pages")
)
del loop


class Version(RequestHandlerCustomError):
    async def get(self):
        version = (await VERSION)[1].decode("utf-8")
        file_hashes = (await FILE_HASHES)[1].decode("utf-8")
        hash_of_file_hashes = hashlib.sha1(file_hashes.encode("utf-8")).hexdigest()
        gh_pages_commit_hash = (await GH_PAGES_COMMIT_HASH)[1].decode("utf-8")
        await self.render(
            "pages/version.html",
            version=version,
            file_hashes=file_hashes,
            hash_of_file_hashes=hash_of_file_hashes,
            gh_pages_commit_hash=gh_pages_commit_hash,
        )
