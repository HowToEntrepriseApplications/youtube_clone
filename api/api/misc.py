import asyncio
from tempfile import NamedTemporaryFile

import aiojobs
from aiohttp import web
from aiohttp.web_exceptions import HTTPFound
from bson import ObjectId

from config import Config
from constants import VIDEO_COLLECTION


async def upload_callback(request: web.Request):
    app = request.app

    video_id = request.match_info['id']

    await app['db'][VIDEO_COLLECTION].update_one({'_id': ObjectId(video_id)}, {'$set': {'uploaded': True}})
    scheduler = aiojobs.aiohttp.get_scheduler_from_app(app)
    await scheduler.spawn(process_file(app, video_id))

    return HTTPFound(app['config'].site.index)


async def process_file(app, video_id):
    s3_config: Config.S3Config = app['config'].s3

    with NamedTemporaryFile() as f:
        await app['s3'].download_fileobj(s3_config.bucket, video_id, f)
        f.flush()

        proc = await asyncio.create_subprocess_shell(
            f'file --mime-type -b {f.name}',
            stdout=asyncio.subprocess.PIPE
        )
        await proc.wait()
        data = await proc.stdout.readline()
        mime_type = data.decode('ascii').rstrip()

    await app['db'][VIDEO_COLLECTION].update_one(
        {'_id': ObjectId(video_id)},
        {'$set': {'uploaded': True, 'mime_detected': True, 'mime_type': mime_type}}
    )
