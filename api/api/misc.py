import asyncio
from tempfile import NamedTemporaryFile

import aiojobs
from aiohttp import web
from aiohttp.web_exceptions import HTTPFound
from bson import ObjectId

from config import Config
from constants import VIDEO_MONGO_COLLECTION, PREVIEW_S3_FOLDER, VIDEO_S3_FOLDER


async def upload_callback(request: web.Request):
    app = request.app

    video_id = request.match_info['id']

    await app['db'][VIDEO_MONGO_COLLECTION].update_one({'_id': ObjectId(video_id)}, {'$set': {'uploaded': True}})
    scheduler = aiojobs.aiohttp.get_scheduler_from_app(app)
    await scheduler.spawn(process_file(app, video_id))

    return HTTPFound(app['config'].site.index)


async def process_file(app, video_id):
    s3_config: Config.S3Config = app['config'].s3

    with NamedTemporaryFile() as video_file:
        await app['s3'].download_fileobj(s3_config.bucket, f'{VIDEO_S3_FOLDER}/{video_id}', video_file)
        video_file.flush()

        # TODO: Добавить нормальную обработку ошибок
        proc = await asyncio.create_subprocess_shell(
            f'file --mime-type -b {video_file.name}',
            stdout=asyncio.subprocess.PIPE
        )
        await proc.wait()
        data = await proc.stdout.readline()
        mime_type = data.decode('ascii').rstrip()

        await app['db'][VIDEO_MONGO_COLLECTION].update_one(
            {'_id': ObjectId(video_id)},
            {'$set': {'mime_type': mime_type}}
        )

        with NamedTemporaryFile() as video_preview_file:
            # TODO: Добавить нормальную обработку ошибок. файл в stdout
            cmd = f'ffmpeg -i "{video_file.name}" -vframes 1 -c:v png -f image2pipe - >  {video_preview_file.name}'
            proc = await asyncio.create_subprocess_shell(
                cmd
            )
            await proc.wait()
            video_preview_file.flush()

            await app['s3'].upload_fileobj(video_preview_file, s3_config.bucket, f'{PREVIEW_S3_FOLDER}/{video_id}')

            await app['db'][VIDEO_MONGO_COLLECTION].update_one(
                {'_id': ObjectId(video_id)},
                {'$set': {'preview_created': True}}
            )
