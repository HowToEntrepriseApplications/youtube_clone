import logging

import aioboto3
import aiohttp_csrf
import aiohttp_session
import aioredis
import botocore
from aiohttp import ClientConnectionError
from aiohttp_security import AbstractAuthorizationPolicy
from aiohttp_security import SessionIdentityPolicy
from aiohttp_security import setup as setup_security
from aiohttp_session import redis_storage
from keycloak.aio import KeycloakOpenidConnect
from keycloak.aio import KeycloakRealm
from motor import motor_asyncio

from common.middlewares import authorized_middleware
from config import Config
from constants import CSRF_FORM_FIELD_NAME

CSRF_SESSION_NAME = 'csrf_token'


logger = logging.getLogger(__name__)


class KeycloakAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, keycloak_connection):
        self._keycloak_connection: KeycloakOpenidConnect = keycloak_connection

    async def authorized_userid(self, identity):
        try:
            user_info = await self._keycloak_connection.userinfo(identity)
        except ClientConnectionError:
            return None

        return identity

    async def permits(self, identity, permission, context=None):
        return True


async def mongo_ctx(app):
    mongo_config: Config.mongo = app['config'].mongo

    client = motor_asyncio.AsyncIOMotorClient(mongo_config.uri)
    app['db'] = client[mongo_config.database]

    yield


async def s3_ctx(app):
    s3_config: Config.S3Config = app['config'].s3

    s3 = aioboto3.client(
        "s3",
        endpoint_url=s3_config.endpoint_url,
        aws_access_key_id=s3_config.aws_access_key_id,
        aws_secret_access_key=s3_config.aws_secret_access_key,
    )
    async with s3 as s3:
        try:
            await s3.head_bucket(Bucket=s3_config.bucket)
        except botocore.exceptions.ClientError:
            logger.info(f'Bucket {s3_config.bucket} created')
            await s3.create_bucket(Bucket=s3_config.bucket)

        app['s3'] = s3

        yield


async def session_ctx(app):
    redis_config: Config.RedisConfig = app['config'].redis
    pool = await aioredis.create_pool(redis_config.uri)
    aiohttp_session.setup(app, redis_storage.RedisStorage(pool))

    yield

    pool.close()
    await pool.wait_closed()


async def csrf_ctx(app):
    csrf_policy = aiohttp_csrf.policy.FormPolicy(CSRF_FORM_FIELD_NAME)
    csrf_storage = aiohttp_csrf.storage.SessionStorage(CSRF_SESSION_NAME)
    aiohttp_csrf.setup(app, policy=csrf_policy, storage=csrf_storage)

    app.middlewares.append(aiohttp_csrf.csrf_middleware)

    yield


async def keycloak_ctx(app):
    keycloak_config: Config.Keycloak = app['config'].keycloak

    realm_params = dict(
        server_url=keycloak_config.server_url,
        realm_name=keycloak_config.realm_name
    )

    connect_params = dict(
        client_id=keycloak_config.client_id,
        client_secret=keycloak_config.client_secret
    )

    async with KeycloakRealm(**realm_params) as realm:
        async with realm.open_id_connect(**connect_params) as connect:
            app['keycloak_connect'] = connect

            setup_security(app,
                           SessionIdentityPolicy(),
                           KeycloakAuthorizationPolicy(connect))
            app.middlewares.append(authorized_middleware)

        yield
