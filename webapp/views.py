import asyncio
from tempfile import NamedTemporaryFile

import aiohttp_jinja2
import aiojobs
import aiojobs.aiohttp
from aiohttp import web
from aiohttp.web_exceptions import HTTPFound
from aiohttp_security import check_authorized
from aiohttp_security import remember, forget
from bson import ObjectId
from keycloak.aio import KeycloakOpenidConnect

from config import Config
from constants import VIDEO_COLLECTION


@aiohttp_jinja2.template('index.html')
async def index(request: web.Request):
    app = request.app

    videos = [
        {'id': str(video['_id']), 'name': video['name']}
        async for video
        in app['db'][VIDEO_COLLECTION].find({'uploaded': True, 'mime_detected': True})
    ]

    return {'videos': videos}


async def auth(request: web.Request):
    app = request.app

    keycloak_connection: KeycloakOpenidConnect = app['keycloak_connect']
    site: Config.SiteConfig = app['config'].site

    callback_url = site.absolute_url.with_path(app.router['callback'].url_for().path)

    auth_url = keycloak_connection.authorization_url(redirect_uri=str(callback_url))
    return HTTPFound(auth_url)


async def auth_callback(request: web.Request):
    app = request.app
    keycloak_connection: KeycloakOpenidConnect = app['keycloak_connect']
    site: Config.SiteConfig = app['config'].site

    code = request.query.get('code')

    callback_url = site.absolute_url.with_path(app.router['callback'].url_for().path)

    responses = await keycloak_connection.authorization_code(code, str(callback_url))

    response = HTTPFound(app.router['index'].url_for())

    await remember(request, response, responses['access_token'])

    return response


async def logout(request: web.Request):
    app = request.app
    response = HTTPFound(app.router['index'].url_for())
    await forget(request, response)
    return response


@aiohttp_jinja2.template('video.html')
async def get_video(request: web.Request):
    app = request.app

    video_id = request.match_info['id']
    video = await app['db'][VIDEO_COLLECTION].find_one(
        {'_id': ObjectId(video_id), 'uploaded': True, 'mime_detected': True}
    )
    url = await app['s3'].generate_presigned_url(
        'get_object',
        Params={'Bucket': app['config'].s3.bucket, 'Key': video_id},
    )
    return {'video': video, 'mime_type': video['mime_type'], 'video_content_url': url}


@aiohttp_jinja2.template('upload.html')
async def upload(request: web.Request):
    await check_authorized(request)

    app = request.app
    site_config: Config.SiteConfig = app['config'].site
    s3_config: Config.S3Config = app['config'].s3

    document = await app['db'][VIDEO_COLLECTION].insert_one({'name': 'undefined'})
    _id = str(document.inserted_id)

    site_url = site_config.absolute_url
    success_action_redirect = str(site_url.join(app.router['upload_callback'].url_for(id=_id)))

    presigned = await app['s3'].generate_presigned_post(
        s3_config.bucket,
        _id,
        Fields={'success_action_redirect': success_action_redirect},
        Conditions=[{'success_action_redirect': success_action_redirect}],
    )

    return {'presigned': presigned}


async def upload_callback(request: web.Request):
    app = request.app

    video_id = request.match_info['id']

    await app['db'][VIDEO_COLLECTION].update_one({'_id': ObjectId(video_id)}, {'$set': {'uploaded': True}})
    scheduler = aiojobs.aiohttp.get_scheduler_from_app(app)
    await scheduler.spawn(process_file(app, video_id))

    return HTTPFound(app.router['index'].url_for())


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
