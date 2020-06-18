from pydantic import BaseModel
from typing import List

from provisioning.app.common.bbox import BBOX
from provisioning.app.tilemill.ProjectLayer import ProjectLayer

class ProjectProperties(BaseModel):
    layers: List[ProjectLayer]
    mss: str
    bbox: BBOX
    zoom_min: int
    zoom_max: int
    name: str
