import logging

import aioboto3
import botocore
from aiohttp import ClientConnectionError
from aiohttp_security import AbstractAuthorizationPolicy, AbstractIdentityPolicy
from aiohttp_security import setup as setup_security
from keycloak.aio import KeycloakOpenidConnect
from keycloak.aio import KeycloakRealm
from motor import motor_asyncio

from config import Config

logger = logging.getLogger(__name__)


AUTH_HEADER_NAME = 'Authorization'
AUTH_SCHEME = 'Bearer '


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
            await s3.create_bucket(Bucket=s3_config.bucket)
            logger.info(f'Bucket {s3_config.bucket} created')

        app['s3'] = s3

        yield


class KeycloakIdentityPolicy(AbstractIdentityPolicy):
    def __init__(self, keycloak_connection):
        self._keycloak_connection: KeycloakOpenidConnect = keycloak_connection

    async def identify(self, request):
        header_identity = request.headers.get(AUTH_HEADER_NAME)

        if header_identity is None:
            return

        if not header_identity.startswith(AUTH_SCHEME):
            raise ValueError('Invalid authorization scheme. ' +
                             'Should be `Bearer <token>`')

        token = header_identity.split(' ')[1].strip()

        try:
            identity = await self._keycloak_connection.userinfo(token)
        except ClientConnectionError:
            return None
        return identity

    async def remember(self, *args, **kwargs):  # pragma: no cover
        pass

    async def forget(self, request, response):  # pragma: no cover
        pass


class KeycloakAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, keycloak_connection):
        self._keycloak_connection: KeycloakOpenidConnect = keycloak_connection

    async def authorized_userid(self, identity):
        return identity

    async def permits(self, identity, permission, context=None):
        return True


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
                           KeycloakIdentityPolicy(connect),
                           KeycloakAuthorizationPolicy(connect))

        yield
