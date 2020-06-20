import environ
from yarl import URL


@environ.config(prefix='')
class Config:
    @environ.config
    class S3Config:
        endpoint_url = environ.var('http://localhost:9000')
        aws_access_key_id = environ.var('minio_access_key')
        aws_secret_access_key = environ.var('minio_secret_key')
        bucket = environ.var('videos')
    s3 = environ.group(S3Config)

    @environ.config
    class MongoConfig:
        uri = environ.var('mongodb://localhost:27017')
        database = environ.var('boringart')
    mongo = environ.group(MongoConfig)

    @environ.config
    class SiteConfig:
        scheme = environ.var('http')
        host = environ.var('0.0.0.0')
        port = environ.var('8000')

        @property
        def absolute_url(self):
            absolute_url = URL.build(scheme=self.scheme, host=self.host, port=self.port)
            if absolute_url.is_default_port():
                absolute_url = absolute_url.with_port(None)
            return absolute_url
    site = environ.group(SiteConfig)
