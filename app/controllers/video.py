from dataclasses import dataclass
from flask_restx import Namespace
from flask_restx import Resource
from flask import request
from app.models.video import Video
from app.models.video import View
from app.models.video import Clap
from app.models.video import Bookmark
from app.models.video import User
from app.models.video import VersionedModel
import datetime
import cachetools.func
from google.cloud import storage
from uuid import uuid4
import os

api = Namespace("api")

@cachetools.func.ttl_cache(maxsize=128, ttl=29 * 60)
def get_url(bucket_name, blob_name, cache, version, expiration=30, method=None, response_type=None, content_type=None, bucket_bound_hostname=None):
    storage_client = storage.Client.from_service_account_json(
        "auth.json"
    ) 
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(
        version=version,
        expiration=expiration,
        method=method,
        response_type=response_type,
        content_type=content_type,
        bucket_bound_hostname=bucket_bound_hostname,
    ), blob.public_url

@dataclass
class BucketObject:
    signed_url: str
    public_url: str
    id: str

def generate_download_signed_url_v4(
        bucket_name: str,
        blob_name: str = None,
        timeout: int = 30,
        cdn_url: str = None,
        prefix: str = None,
        extension: str = None,
        is_uploading_video: bool = False,
        is_downloading_video: bool = False,
        content_type: str = "video/mp4",
        method: str = "PUT") -> BucketObject:
    """Generates a v4 signed URL for downloading a blob.

    Note that this method requires a service account key file. You can not use
    this if you are using Application Default Credentials from Google Compute
    Engine or from the Google Cloud SDK.

    Timeout is in minutes.
    """
    if not blob_name:
        blob_name = access_code_generator()

    if extension:
        blob_name = f"{blob_name}.{extension}"

    if prefix:
        blob_name = f"{prefix}.{blob_name}"

    
    config = dict(
        version="v4",
        expiration=datetime.timedelta(minutes=timeout),
        method=method,
    )

    if is_downloading_video:
        config["response_type"] = content_type

    if is_uploading_video:
        config["content_type"] = content_type

    if cdn_url:
        config["bucket_bound_hostname"] = cdn_url

    url, public_url = get_url(bucket_name, blob_name, "True", **config)

    return BucketObject(
        id=blob_name,
        signed_url=url,
        public_url=public_url
    )


def video_urls(video):
    video_id = video.get("video_path")
    signed_video = None
    signed_captions = None
    signed_gif = None
    signed_thumbnail = None

    # If the video was processed, return the processed stream, otherwise return the original str
    if video.get("update_complete"):

        signed_video = generate_download_signed_url_v4(
            bucket_name="development.videos.static.processed.claps.ai",
            blob_name=f"{video_id}/video.mp4",
            method="GET",
            is_downloading_video=True,
            timeout=120,  # 120 minutes,
            cdn_url=None
        )

    else:
        signed_video = generate_download_signed_url_v4(
            bucket_name="development.videos.static.claps.ai",
            blob_name=video_id,
            method="GET",
            is_downloading_video=True,
            timeout=120,  # 120 minutes,
            cdn_url=None#bucket_to_cdn("development.videos.static.claps.ai")
        )

    if video.get("update_complete"):
        signed_gif = ""#f"https://storage.googleapis.com/{current_app.config.get('GOOGLE_PUBLIC_BUCKET')}/{video_id}/preview.gif"

        signed_thumbnail = ""#f"https://storage.googleapis.com/{current_app.config.get('GOOGLE_PUBLIC_BUCKET')}/{video_id}/thumb.png"

        signed_captions = generate_download_signed_url_v4(
            bucket_name="development.videos.static.processed.claps.ai",
            blob_name=f"{video_id}/subs.vtt",
            method="GET",
            is_downloading_video=True,
            content_type="text/vtt",
            timeout=120,  # 120 minutes,
            cdn_url=None
        )

    return (signed_video, signed_gif, signed_thumbnail, signed_captions)

@api.route("/real")
class RealController(Resource):
    def get(self):
        query = """
            select 
                v.id,
                v.video_path,
                v.user_tag,
                v.title, 
                if(v2.id, true, false) as seen,
                if(c.id, true, false) as clapped,
                if(b.id, true, false) as bookmarked
            from videos v 
            left join views v2 on v2.video_id = v.id and (v2.user_id = '19973')
            left join claps c on c.video_id = v.id and (c.user_id = '19973')
            left join bookmarks b on b.video_id = v.id and (b.user_id = '19973')
            order by field(v.user_tag, "data science") desc
            limit 10 offset 0;            
        """

        data = VersionedModel.fetchall_dict(query)
        for x in data:
            urls = video_urls(x)
            x.update({
                "url": urls[0].signed_url,
                "gif": urls[1],
                "thumbnail": urls[2],
                # "captions": urls[3].signed_url
            })

        return data


@api.route("")
class VideoController(Resource):
    def get(self):
        return [x.get_for_api() for x in Video.get_all("*", limit=5)]

    def post(self):
        return Video(**request.get_json()).save().get_for_api()


@api.route("/view")
class ViewController(Resource):
    def get(self):
        return [x.get_for_api() for x in View.get_all("*")]

    def post(self):
        return View(**request.get_json()).save().get_for_api()


@api.route("/clap")
class ClapController(Resource):
    def get(self):
        return [x.get_for_api() for x in Clap.get_all("*")]

    def post(self):
        return Clap(**request.get_json()).save().get_for_api()



@api.route("/bookmark")
class BookmarkController(Resource):
    def get(self):
        return [x.get_for_api() for x in Bookmark.get_all("*")]

    def post(self):
        return Bookmark(**request.get_json()).save().get_for_api()



@api.route("/user")
class UserController(Resource):
    def get(self):
        return [x.get_for_api() for x in User.get_all("*")]

    def post(self):
        return User(**request.get_json()).save().get_for_api()


