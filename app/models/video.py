from app.models import VersionedModel

class Video(VersionedModel):
    __tablename__ = "video"

    id: str
    title: str
    user_id: str
    user_tag: str
    deleted: bool
    original_content: bool
    update_complete: bool

class View(VersionedModel):
    __tablename__ = "view"

    video_id: str
    user_id: str

class Clap(VersionedModel):
    __tablename__ = "clap"

    video_id: str
    user_id: str    

class Bookmark(VersionedModel):
    __tablename__ = "bookmark"

    video_id: str
    user_id: str        

class User(VersionedModel):
    __tablename__ = "user"

    id: str
    device_id:  str
    nick:  str
    name:  str
    interest: str