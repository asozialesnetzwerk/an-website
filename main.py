import web
from discord.discord import Discord

urls = (
    '/discord/', 'Discord'
)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()