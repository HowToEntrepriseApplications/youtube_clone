import logging
import uuid

import aioboto3
import botocore
import environ
from aiohttp import web
from bson import ObjectId
from motor import motor_asyncio

from config import Config


logger = logging.getLogger(__name__)


async def get_videos(request: web.Request):
    app = request.app

    videos = []
    async for video in app['db']['videos'].find():
        videos.append((video['_id'], video['name']))

    videos_html = '\n'.join(
        '<div><h3><a href="/{id_}">{name}</a></h3></div>'.format(id_=id_, name=name)
        for id_, name in videos
    )

    html = f"""
<!DOCTYPE html>
<html>
    <body>
        <h1>Youtube clone</h1>
        <h2>Upload video</h2>
        <form action="/" method="post" accept-charset="utf-8" enctype="multipart/form-data">
            <input id="video" name="video" type="file" value=""/>
            <input type="submit" value="submit"/>
        </form>
        <br>
        <h2>Videos:</h2>
        {videos_html}
    </body>
</html>
"""

    return web.Response(body=html, content_type='text/html')


async def get_video(request: web.Request):
    app = request.app

    video_id = request.match_info['id']
    video = await app['db']['videos'].find_one({'_id': ObjectId(video_id)})

    url = await app['s3'].generate_presigned_url(
        'get_object',
        Params={'Bucket': app['config'].s3.bucket, 'Key': video['key']},
    )

    html = f"""
<!DOCTYPE html>
<html>
    <body>
        <h1><a href="/">youtube clone</a></h1>
        <h2>{video["name"]}</h2>
        <video controls>
            <source src="{url}" type="video/mp4">
        <video>
    </body>
</html>
"""

    return web.Response(body=html, content_type='text/html')


async def post_video(request: web.Request):
    app = request.app
    data = await request.post()
    video = data['video']

    key = f'{uuid.uuid4()}'
    await app['s3'].upload_fileobj(
        Fileobj=video.file,
        Bucket=app['config'].s3.bucket,
        Key=key,
    )
    result = await app['db']['videos'].insert_one({'name': video.filename, 'key': key})

    return web.HTTPFound(f'/{result.inserted_id}')


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


async def mongo_ctx(app):
    mongo_config: Config.mongo = app['config'].mongo

    client = motor_asyncio.AsyncIOMotorClient(
        mongo_config.uri,
        username=mongo_config.username,
        password=mongo_config.password,
    )
    app['db'] = client[mongo_config.database]

    yield


def main():
    print(environ.generate_help(Config, display_defaults=True))
    config = environ.to_config(Config)

    app = web.Application()
    app['config'] = config

    app.cleanup_ctx.extend((s3_ctx, mongo_ctx))
    app.add_routes([
        web.get('', get_videos),
        web.get('/{id}', get_video),
        web.post('/', post_video),
    ])

    web.run_app(app)


if __name__ == '__main__':
    main()
