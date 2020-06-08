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
        async for video
        in app['db'][VIDEO_COLLECTION].find({'uploaded': True})
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
    video = await app['db'][VIDEO_COLLECTION].find_one({'_id': ObjectId(video_id), 'uploaded': True})
    url = await app['s3'].generate_presigned_url(
        'get_object',
        Params={'Bucket': app['config'].s3.bucket, 'Key': video_id},
    )
    return {'video': video, 'video_content_url': url}


@aiohttp_jinja2.template('upload.html')
async def upload(request: web.Request):
    await check_authorized(request)

    app = request.app
    site_config: Config.SiteConfig = app['config'].site

    document = await app['db'][VIDEO_COLLECTION].insert_one({'name': 'undefined'})
    _id = str(document.inserted_id)

    site_url = site_config.absolute_url
    success_action_redirect = str(site_url.join(app.router['upload_callback'].url_for(id=_id)))

    presigned = await app['s3'].generate_presigned_post(
        app['config'].s3.bucket,
        _id,
        Fields={'success_action_redirect': success_action_redirect},
        Conditions=[{'success_action_redirect': success_action_redirect}],
    )

    return {'presigned': presigned}


async def upload_callback(request: web.Request):
    app = request.app

    video_id = request.match_info['id']

    await app['db'][VIDEO_COLLECTION].update_one({'_id': ObjectId(video_id)}, {'$set': {'uploaded': True}})

    return HTTPFound(app.router['video'].url_for(id=video_id))
