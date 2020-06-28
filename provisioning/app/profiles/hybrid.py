from typing import List, Tuple

from app.common.bbox import BBOX
from app.profiles.Profile import Profile
from app.sources.canvec_wms import provision as canvec_wms_provisioner, OUTPUT_CRS_CODE as canvec_crs_code, OUTPUT_TYPE as canvec_output_type
from app.sources.bc_hillshade import provision as bc_hillshade_provisioner, OUTPUT_CRS_CODE as bc_hillshade_crs_code, OUTPUT_TYPE as bc_hillshade_output_type
from app.sources.bc_resource_roads import provision as bc_resource_roads_provisioner, OUTPUT_CRS_CODE as bc_resource_roads_crs_code, OUTPUT_TYPE as bc_resource_roads_output_type
from app.sources.bc_topo_20000 import provision as bc_topo_20000_provisioner, OUTPUT_CRS_CODE as bc_topo_crs_code, OUTPUT_TYPE as bc_topo_output_type
from app.sources.shelters import provision as shelters_provisioner, OUTPUT_CRS_CODE as shelters_crs_code, OUTPUT_TYPE as shelters_output_type
from app.sources.trails import provision as trails_provisioner, OUTPUT_CRS_CODE as trails_crs_code, OUTPUT_TYPE as trails_output_type
from app.tilemill.ProjectLayer import ProjectLayer


def get_profile(bbox: BBOX, run_id: str) -> Profile:

    def canvec() -> List[ProjectLayer]:
        layer_lists = [
            [
                ProjectLayer(path=file, style_class=f"canvec-{scale}", crs_code=canvec_crs_code, type=canvec_output_type)
                for file in files
            ]
            for scale, files in canvec_wms_provisioner(
                bbox,
                (10000000, 4000000, 2000000, 1000000, 500000, 250000, 150000, 70000, 35000),
                run_id
            ).items()
        ]
        return [item for sublist in layer_lists for item in sublist]

    def bc_topo_20000() -> List[ProjectLayer]:
        return [
            ProjectLayer(path=file, style_class="bc-topo-20000", crs_code=bc_topo_crs_code, type=bc_topo_output_type)
            for file in bc_topo_20000_provisioner(bbox, run_id)
        ]

    def bc_hillshade() -> List[ProjectLayer]:
        return [
            ProjectLayer(path=file, style_class="bc-hillshade", crs_code=bc_hillshade_crs_code, type=bc_hillshade_output_type)
            for file in bc_hillshade_provisioner(bbox, run_id)
        ]

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
        provisioners=(canvec, bc_topo_20000, bc_hillshade, bc_resource_roads, trails, shelters),
        stylesheets=("common", "hybrid"),
        zooms=(0, 17),
        zooms_xyz=(16, 17)
    )
