import logging

import aioboto3
import botocore
import environ
from aiohttp import web
from motor import motor_asyncio

from config import Config


logger = logging.getLogger(__name__)


async def get_videos(request: web.Request):
    html = """
<!DOCTYPE html>
<html>
    <body>
        <h1>youtube clone</h1>
        <h2>Videos:</h2>
        <div>
            <h3><a href="/1">Big buck bunny</a></h3>
        </div>
    <br>
    </body>
</html>
"""

    return web.Response(body=html, content_type='text/html')


async def get_video(request: web.Request):
    html = """
<!DOCTYPE html>
<html>
    <body>
        <h1><a href="/">youtube clone</a></h1>
        <h2>Big buck bunny</h2>
        <video controls src="https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4">
        <br>
        youtube_clone
    </body>
</html>
"""

    return web.Response(body=html, content_type='text/html')


async def s3_ctx(app):
    s3_config: Config.S3Config = app['config'].s3

    s3 = aioboto3.client(
        "s3",
        endpoint_url=s3_config.endpoint_url,
        aws_access_key_id=s3_config.aws_access_key_id,
        aws_secret_access_key=s3_config.aws_secret_access_key
    )
    async with s3 as s3:
        try:
            await s3.head_bucket(Bucket=s3_config.bucket)
        except botocore.exceptions.ClientError:
            logger.info(f'Bucket {s3_config.bucket} created')
            await s3.create_bucket(Bucket=s3_config.bucket)

        app['s3'] = s3

        yield


async def mongo_ctx(app):
    mongo_config: Config.mongo = app['config'].mongo

    client = motor_asyncio.AsyncIOMotorClient(mongo_config.uri)
    app['db'] = client[mongo_config.database]

    yield


def main():
    print(environ.generate_help(Config, display_defaults=True))
    config = environ.to_config(Config)

    app = web.Application()
    app['config'] = config

    app.cleanup_ctx.extend((s3_ctx, ))
    app.add_routes([
        web.get('', get_videos),
        web.get('/1', get_video)
    ])

    web.run_app(app)


if __name__ == '__main__':
    main()
