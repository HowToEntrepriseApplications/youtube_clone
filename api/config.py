import environ
from yarl import URL


@environ.config(prefix='')
class Config:
    @environ.config
    class S3Config:
        endpoint_url = environ.var('http://localhost:9000')
        aws_access_key_id = environ.var('minio_access_key')
        aws_secret_access_key = environ.var('minio_secret_key')
        bucket = environ.var('boringart')
    s3 = environ.group(S3Config)

    @environ.config
    class MongoConfig:
        uri = environ.var('mongodb://localhost:27017')
        database = environ.var('boringart')
    mongo = environ.group(MongoConfig)

    @environ.config
    class Keycloak:
        server_url = environ.var('http://localhost:8080')
        realm_name = environ.var('boringart')
        client_id = environ.var('api')
        client_secret = environ.var()
    keycloak = environ.group(Keycloak)

    @environ.config
    class APIConfig:
        scheme = environ.var('http')
        host = environ.var('0.0.0.0')
        port = environ.var('8000')

        @property
        def absolute_url(self):
            absolute_url = URL.build(scheme=self.scheme, host=self.host, port=self.port)
            if absolute_url.is_default_port():
                absolute_url = absolute_url.with_port(None)
            return absolute_url
    api = environ.group(APIConfig)

    @environ.config
    class SiteConfig:
        index = environ.var('http://localhost:3000')
    site = environ.group(SiteConfig)
