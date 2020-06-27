from pathlib import Path

import aiohttp_cors
import aiojobs
import aiojobs.aiohttp
import environ
from aiohttp.web import Application
from aiohttp_graphql import GraphQLView
from graphql.execution.executors.asyncio import AsyncioExecutor

from cleanup_ctx import mongo_ctx, s3_ctx, keycloak_ctx
from config import Config
from api.graphql_schema import schema
from api.misc import upload_callback

BASE_DIR = Path(__file__).parent


def get_app(extra_argv=None) -> Application:
    config = environ.to_config(Config)

    app = Application()
    app['config'] = config
    aiojobs.aiohttp.setup(app, limit=1)

    app.cleanup_ctx.extend((s3_ctx, mongo_ctx, keycloak_ctx))

    cors = aiohttp_cors.setup(app)
    resource = cors.add(app.router.add_resource("/graphql"), {
        "*": aiohttp_cors.ResourceOptions(
            expose_headers="*",
            allow_headers="*",
            allow_credentials=True,
            allow_methods=["POST", "PUT", "GET"]),
    })
    GraphQLView(schema=schema, graphiql=True, executor=AsyncioExecutor())
    resource.add_route("*", GraphQLView(schema=schema, graphiql=True, executor=AsyncioExecutor()))
    app.router.add_get('/upload_callback/{id}', upload_callback, name='upload_callback')

    return app


def get_dev_app(extra_argv=None) -> Application:
    app = get_app(extra_argv)
    return app
