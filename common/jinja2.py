from typing import Dict, Any

import aiohttp_csrf
import jinja2
from aiohttp_csrf.storage import REQUEST_NEW_TOKEN_KEY


@jinja2.contextfunction
def csrf_token(context: Dict[str, Any]):
    request = context['request']
    storage = aiohttp_csrf._get_storage(request)

    if REQUEST_NEW_TOKEN_KEY in request:
        return request[REQUEST_NEW_TOKEN_KEY]

    token = storage._generate_token()

    request[REQUEST_NEW_TOKEN_KEY] = token

    return token


@jinja2.contextfunction
def authorized(context: Dict[str, Any]):
    request = context['request']
    return request['authorized']
