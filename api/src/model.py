from enum import Enum
from pydantic import BaseModel
from typing import Optional, List


DEFAULT_UID = "425f6781-e42b-23e2-a341-2431564214523"


class FileType(str, Enum):
    uri = "uri"
    dir = "dir"
    file = "file"


class Location(str, Enum):
    splash = "splash"
    local = "local"
    tiled = "tiled"


class DataPath(BaseModel):
    file_path: List[str]
    file_type: FileType
    file_location: Location


class Dataset(BaseModel):
    uid: str = DEFAULT_UID
    user_id: Optional[str]
    datapath: DataPath
    labelpath: Optional[DataPath]
