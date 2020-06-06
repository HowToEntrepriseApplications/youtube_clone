import environ
from yarl import URL


@environ.config(prefix='')
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

    @environ.config
    class RedisConfig:
        uri = environ.var('redis://localhost:6380/1')
    redis = environ.group(RedisConfig)

    @environ.config
    class SiteConfig:
        scheme = environ.var('http')
        host = environ.var('0.0.0.0')
        port = environ.var('8000')
        name = environ.var('Youtube clone')

        @property
        def absolute_url(self):
            return URL.build(scheme=self.scheme, host=self.host, port=self.port)
    site = environ.group(SiteConfig)

    @environ.config
    class Keycloak:
        server_url = environ.var('http://localhost:8082')
        realm_name = environ.var('youtube_clone')
        client_id = environ.var('webapp')
        client_secret = environ.var('5106d698-2ea4-457b-a99e-8ba1952ae674')
    keycloak = environ.group(Keycloak)
