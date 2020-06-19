from pydantic import BaseModel

from provisioning.app.tilemill.ProjectLayerType import ProjectLayerType

class ProjectLayer(BaseModel):
    path: str
    style_class: str
    crs_code: str
    type: ProjectLayerType
