import logging

import aioboto3
import botocore
from motor import motor_asyncio

from config import Config


logger = logging.getLogger(__name__)


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
