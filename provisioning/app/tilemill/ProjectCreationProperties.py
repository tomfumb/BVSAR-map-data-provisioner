from typing import List

from app.tilemill.ProjectLayer import ProjectLayer
from app.tilemill.ProjectProperties import ProjectProperties


class ProjectCreationProperties(ProjectProperties):
    layers: List[ProjectLayer]
    mss: List[str]
