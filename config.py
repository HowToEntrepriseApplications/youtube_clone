import environ


@environ.config(prefix='YC')
class Config:
    @environ.config
    class S3Config:
        endpoint_url = environ.var('http://localhost:9000')
        aws_access_key_id = environ.var('minio_access_key')
        aws_secret_access_key = environ.var('minio_secret_key')
        bucket = environ.var('youtube-clone')
    s3 = environ.group(S3Config)

    @environ.config
    class MongoConfig:
        uri = environ.var('mongodb://localhost:27017')
        database = environ.var('youtube_clone')
    mongo = environ.group(MongoConfig)
