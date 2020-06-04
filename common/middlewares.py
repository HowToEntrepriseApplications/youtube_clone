from aiohttp import web
from aiohttp_security import authorized_userid


@web.middleware
async def authorized_middleware(request, handler):
    authorized = await authorized_userid(request)

    request['authorized'] = authorized

    return await handler(request)
