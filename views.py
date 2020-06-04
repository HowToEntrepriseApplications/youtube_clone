import uuid

import aiohttp_jinja2
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
        async for video in app['db'][VIDEO_COLLECTION].find()
    ]

    return {'videos': videos}


async def auth(request: web.Request):
    app = request.app

    keycloak_connection: KeycloakOpenidConnect = app['keycloak_connect']
    site: Config.SiteConfig = app['config'].site

    callback_url = site.absolute_url.with_path(app.router['callback'].url_for().path)

    auth_url = keycloak_connection.authorization_url(redirect_uri=str(callback_url))
    return HTTPFound(auth_url)


async def callback(request: web.Request):
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
    video = await app['db'][VIDEO_COLLECTION].find_one({'_id': ObjectId(video_id)})
    url = await app['s3'].generate_presigned_url(
        'get_object',
        Params={'Bucket': app['config'].s3.bucket, 'Key': video['key']},
    )
    return {'video': video, 'video_content_url': url}


async def post_video(request: web.Request):
    await check_authorized(request)

    app = request.app
    data = await request.post()
    video = data['video']

    key = f'{uuid.uuid4()}'
    await app['s3'].upload_fileobj(
        Fileobj=video.file,
        Bucket=app['config'].s3.bucket,
        Key=key,
    )
    result = await app['db'][VIDEO_COLLECTION].insert_one({'name': video.filename, 'key': key})

    return web.HTTPFound(app.router['video'].url_for(id=str(result.inserted_id)))