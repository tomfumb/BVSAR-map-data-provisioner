from pydantic import BaseModel
from typing import List

from app.common.BBOX import BBOX
from app.tilemill.ProjectLayer import ProjectLayer

class ProjectProperties(BaseModel):
    bbox: BBOX
    zoom_min: int
    zoom_max: int
    name: str
