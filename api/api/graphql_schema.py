from bson import ObjectId
from graphene import ObjectType, String, Schema, ID, Field, List, JSONString

from config import Config
from constants import VIDEO_MONGO_COLLECTION, VIDEO_S3_FOLDER, PREVIEW_S3_FOLDER


class Video(ObjectType):
    id = ID()
    title = String()
    mime_type = String()
    content_url = String()
    preview_url = String()

    @staticmethod
    async def resolve_content_url(root, info):
        app = info.context['request'].app
        return await app['s3'].generate_presigned_url(
            'get_object',
            Params={'Bucket': app['config'].s3.bucket, 'Key': f'{VIDEO_S3_FOLDER}/{root.id}'},
        )

    @staticmethod
    async def resolve_preview_url(root, info):
        app = info.context['request'].app
        return await app['s3'].generate_presigned_url(
            'get_object',
            Params={'Bucket': app['config'].s3.bucket, 'Key': f'{PREVIEW_S3_FOLDER}/{root.id}'},
        )


class Query(ObjectType):
    videos = List(Video)
    get_video_by_id = Field(Video, id=ID())

    @staticmethod
    async def resolve_videos(root, info):
        app = info.context['request'].app
        return [
            Video(id=video['_id'], title=video['title'])
            async for video
            in app['db'][VIDEO_MONGO_COLLECTION].find({'mime_type': {'$exists': True}, 'preview_created': True})
        ]

    @staticmethod
    async def resolve_get_video_by_id(root, info, id):
        app = info.context['request'].app
        video = await app['db'][VIDEO_MONGO_COLLECTION].find_one(
            {'_id': ObjectId(id), 'mime_type': {'$exists': True}, 'preview_created': True}
        )
        return Video(id=str(video['_id']), title=video['title'], mime_type=video['mime_type'])


class Mutations(ObjectType):
    generate_upload_data = JSONString(name=String())

    @staticmethod
    async def resolve_generate_upload_data(root, info, name):
        # TODO: authorize required

        app = info.context['request'].app
        api_config: Config.APIConfig = app['config'].api
        s3_config: Config.S3Config = app['config'].s3

        document = await app['db'][VIDEO_MONGO_COLLECTION].insert_one({'title': name})
        _id = str(document.inserted_id)

        site_url = api_config.absolute_url
        success_action_redirect = str(site_url.join(app.router['upload_callback'].url_for(id=_id)))

        presigned = await app['s3'].generate_presigned_post(
            s3_config.bucket,
            f'{VIDEO_S3_FOLDER}/{_id}',
            Fields={'success_action_redirect': success_action_redirect},
            Conditions=[{'success_action_redirect': success_action_redirect}],
        )

        return presigned


schema = Schema(query=Query, mutation=Mutations)
