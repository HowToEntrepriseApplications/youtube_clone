from pathlib import Path

import aiohttp_debugtoolbar
import aiohttp_jinja2
import aiojobs
import aiojobs.aiohttp
import environ
import jinja2
from aiohttp.web import Application

import views
from cleanup_ctx import mongo_ctx, s3_ctx, session_ctx, csrf_ctx, keycloak_ctx
from jinja2_contextfunction import csrf_token, authorized
from config import Config
from constants import CSRF_FORM_FIELD_NAME

BASE_DIR = Path(__file__).parent


def get_app(extra_argv=None) -> Application:
    config = environ.to_config(Config)

    app = Application()
    app['config'] = config
    aiojobs.aiohttp.setup(app, limit=1)

    jinja2_env = aiohttp_jinja2.setup(
        app,
        context_processors=(aiohttp_jinja2.request_processor, ),
        loader=jinja2.FileSystemLoader((BASE_DIR / 'templates',)),
    )
    jinja2_env.globals['csrf_token'] = csrf_token
    jinja2_env.globals['csrf_name'] = CSRF_FORM_FIELD_NAME
    jinja2_env.globals['authorized'] = authorized

    app.cleanup_ctx.extend((s3_ctx, mongo_ctx, session_ctx, keycloak_ctx, csrf_ctx))

    # index route
    app.router.add_get('', views.index, name='index')

    # auth routes
    app.router.add_route('*', '/auth', views.auth, name='auth')
    app.router.add_route('*', '/oauth2/callback', views.auth_callback, name='callback')
    app.router.add_route('*', '/logout', views.logout, name='logout')

    # user routes

    # upload routes
    app.router.add_get('/upload', views.upload, name='upload')
    app.router.add_get('/upload_callback/{id}', views.upload_callback, name='upload_callback')

    # videos
    app.router.add_get('/video/{id}', views.get_video, name='video')

    return app


def get_dev_app(extra_argv=None) -> Application:
    app = get_app(extra_argv)
    aiohttp_debugtoolbar.setup(app, hosts=['192.168.0.0/16'])
    return app
