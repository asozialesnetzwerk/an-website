from __future__ import annotations

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=(
            (r"/zitate/?", QuoteMainPage),
            # {1,10} is too much, but better too much than not enough
            (r"/zitate/([0-9]{1,10})-([0-9]{1,10})/?", QuoteById),
        ),
        name="Falsch zugeordnete Zitate",
        description="Eine Website mit falsch zugeordneten Zitaten",
        path="/zitate",
    )


def get_quote_by_id(quote_id: int) -> str:
    # do db query here
    return f"{quote_id}, ..."


def get_author_by_id(author_id: int) -> str:
    # do db query here
    return f"Sir {author_id}"


def get_rating_by_ids(quote_id: int, author_id: int) -> int:
    # do db query here
    return 2 * quote_id + 3 * author_id


class Quote(BaseRequestHandler):
    async def render_quote(self, quote_id: int, author_id: int):
        return await self.render(
            "pages/quotes.html",
            quote=get_quote_by_id(quote_id),
            author=get_author_by_id(author_id),
            rating=get_rating_by_ids(quote_id, author_id),
            quote_id=quote_id,
            author_id=author_id,
            id=f"{quote_id}-{author_id}",
            next_href=f"/zitate/{await self.get_next_id()}",
        )

    async def get_next_id(self):
        return "0-0"


class QuoteMainPage(Quote):
    async def get(self):
        await self.render_quote(-1, -1)


class QuoteById(Quote):
    async def get(self, quote_id: int, author_id: int):
        await self.render_quote(quote_id, author_id)
