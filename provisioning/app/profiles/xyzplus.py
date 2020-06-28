from typing import List, Tuple

from app.common.bbox import BBOX
from app.profiles.Profile import Profile
from app.sources.bc_resource_roads import provision as bc_resource_roads_provisioner, OUTPUT_CRS_CODE as bc_resource_roads_crs_code, OUTPUT_TYPE as bc_resource_roads_output_type
from app.sources.shelters import provision as shelters_provisioner, OUTPUT_CRS_CODE as shelters_crs_code, OUTPUT_TYPE as shelters_output_type
from app.sources.trails import provision as trails_provisioner, OUTPUT_CRS_CODE as trails_crs_code, OUTPUT_TYPE as trails_output_type
from app.tilemill.ProjectLayer import ProjectLayer


def get_profile(bbox: BBOX, run_id: str) -> Profile:

    def bc_resource_roads() -> List[ProjectLayer]:
        bc_resource_road_files = bc_resource_roads_provisioner(bbox, run_id)
        return [
            ProjectLayer(path=bc_resource_road_files[0], style_class=class_name, crs_code=bc_resource_roads_crs_code, type=bc_resource_roads_output_type)
            for class_name in ("bc-resource-roads", "bc-resource-roads-label")
        ]

    def trails() -> List[ProjectLayer]:
        return [
            ProjectLayer(path=trails_provisioner(bbox, run_id)[0], style_class="trails", crs_code=trails_crs_code, type=trails_output_type)
        ]

    def shelters() -> List[ProjectLayer]:
        return [
            ProjectLayer(path=shelters_provisioner(bbox, run_id)[0], style_class="shelters", crs_code=shelters_crs_code, type=shelters_output_type)
        ]

    return Profile(
        provisioners=(bc_resource_roads, trails, shelters),
        stylesheets=("common",),
        zooms=(0, 17),
        zooms_xyz=(0, 17)
    )
