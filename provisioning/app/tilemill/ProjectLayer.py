from pydantic import BaseModel

class ProjectLayer(BaseModel):
    path: str
    style_class: str
    crs_code: str
