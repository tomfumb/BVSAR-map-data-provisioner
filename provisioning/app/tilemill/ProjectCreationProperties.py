from typing import List

from provisioning.app.tilemill.ProjectLayer import ProjectLayer
from provisioning.app.tilemill.ProjectProperties import ProjectProperties

class ProjectCreationProperties(ProjectProperties):
    layers: List[ProjectLayer]
    mss: List[str]
