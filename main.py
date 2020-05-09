from aiohttp import web


async def get_videos(request: web.Request):
    html = """
<!DOCTYPE html>
<html>
    <body>
        <h1>youtube clone</h1>
        <h2>Videos:</h2>
        <div>
            <h3><a href="/1">Big buck bunny</a></h3>
        </div>
    <br>
    </body>
</html>
"""

    return web.Response(body=html, content_type='text/html')


async def get_video(request: web.Request):
    html = """
<!DOCTYPE html>
<html>
    <body>
        <h1><a href="/">youtube clone</a></h1>
        <h2>Big buck bunny</h2>
        <video controls src="https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4">
        <br>
        youtube_clone
    </body>
</html>
"""

    return web.Response(body=html, content_type='text/html')


def main():
    app = web.Application()
    app.add_routes([
        web.get('', get_videos),
        web.get('/1', get_video)
    ])

    web.run_app(app)


if __name__ == '__main__':
    main()
