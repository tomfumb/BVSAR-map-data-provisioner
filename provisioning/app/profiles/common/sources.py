from typing import List

from app.common.bbox import BBOX
from app.tilemill.ProjectLayer import ProjectLayer
from app.sources.canvec_wms import (
    provision as canvec_wms_provisioner,
    OUTPUT_CRS_CODE as canvec_crs_code,
    OUTPUT_TYPE as canvec_output_type,
)
from app.sources.bc_hillshade import (
    provision as bc_hillshade_provisioner,
    OUTPUT_CRS_CODE as bc_hillshade_crs_code,
    OUTPUT_TYPE as bc_hillshade_output_type,
)
from app.sources.bc_resource_roads import (
    provision as bc_resource_roads_provisioner,
    OUTPUT_CRS_CODE as bc_resource_roads_crs_code,
    OUTPUT_TYPE as bc_resource_roads_output_type,
)
from app.sources.bc_topo_20000 import (
    provision as bc_topo_20000_provisioner,
    OUTPUT_CRS_CODE as bc_topo_crs_code,
    OUTPUT_TYPE as bc_topo_output_type,
)
from app.sources.shelters import (
    provision as shelters_provisioner,
    OUTPUT_CRS_CODE as shelters_crs_code,
    OUTPUT_TYPE as shelters_output_type,
)
from app.sources.trails import (
    provision as trails_provisioner,
    OUTPUT_CRS_CODE as trails_crs_code,
    OUTPUT_TYPE as trails_output_type,
)
from app.sources.bc_waterways import (
    provision as bc_waterways_provisioner,
    OUTPUT_CRS_CODE as bc_waterways_crs_code,
    OUTPUT_TYPE as bc_waterways_output_type,
)
from app.sources.bc_wetlands import (
    provision as bc_wetlands_provisioner,
    OUTPUT_CRS_CODE as bc_wetlands_crs_code,
    OUTPUT_TYPE as bc_wetlands_output_type,
)
from app.sources.bc_ates_zones import (
    provision as bc_ates_zones_provisioner,
    OUTPUT_CRS_CODE as bc_ates_zones_crs_code,
    OUTPUT_TYPE as bc_ates_zones_output_type,
)
from app.sources.bc_ates_av_paths import (
    provision as bc_ates_av_paths_provisioner,
    OUTPUT_CRS_CODE as bc_ates_av_paths_crs_code,
    OUTPUT_TYPE as bc_ates_av_paths_output_type,
)
from app.sources.bc_ates_dec_points import (
    provision as bc_ates_dec_points_provisioner,
    OUTPUT_CRS_CODE as bc_ates_dec_points_crs_code,
    OUTPUT_TYPE as bc_ates_dec_points_output_type,
)
from app.sources.bc_ates_poi import (
    provision as bc_ates_poi_provisioner,
    OUTPUT_CRS_CODE as bc_ates_poi_crs_code,
    OUTPUT_TYPE as bc_ates_poi_output_type,
)
from app.sources.bc_parcels import (
    provision as bc_parcels_provisioner,
    OUTPUT_CRS_CODE as bc_parcels_crs_code,
    OUTPUT_TYPE as bc_parcels_output_type,
)
from app.sources.bc_rec_sites import (
    provision as bc_rec_sites_provisioner,
    OUTPUT_CRS_CODE as bc_rec_sites_crs_code,
    OUTPUT_TYPE as bc_rec_sites_output_type,
)


def canvec(bbox: BBOX, run_id: str, scales: List[int]) -> List[ProjectLayer]:
    layers = list()
    for scale, files in canvec_wms_provisioner(bbox, scales, run_id).items():
        layers += [
            ProjectLayer(
                path=file,
                style_class=f"canvec-{scale}",
                crs_code=canvec_crs_code,
                type=canvec_output_type,
            )
            for file in files
        ]
    return layers


def bc_topo(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=file,
            style_class="bc-topo-20000",
            crs_code=bc_topo_crs_code,
            type=bc_topo_output_type,
        )
        for file in bc_topo_20000_provisioner(bbox, run_id)
    ]


def bc_hillshade(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=file,
            style_class="bc-hillshade",
            crs_code=bc_hillshade_crs_code,
            type=bc_hillshade_output_type,
        )
        for file in bc_hillshade_provisioner(bbox, run_id)
    ]


def bc_resource_roads(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    bc_resource_road_files = bc_resource_roads_provisioner(bbox, run_id)
    return [
        ProjectLayer(
            path=bc_resource_road_files[0],
            style_class=class_name,
            crs_code=bc_resource_roads_crs_code,
            type=bc_resource_roads_output_type,
        )
        for class_name in ("bc-resource-roads", "bc-resource-roads-label")
    ]


def trails(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=trails_provisioner(bbox, run_id)[0],
            style_class="trails",
            crs_code=trails_crs_code,
            type=trails_output_type,
        )
    ]


def shelters(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=shelters_provisioner(bbox, run_id)[0],
            style_class="shelters",
            crs_code=shelters_crs_code,
            type=shelters_output_type,
        )
    ]


def bc_waterways(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=bc_waterways_provisioner(bbox, run_id)[0],
            style_class="waterways",
            crs_code=bc_waterways_crs_code,
            type=bc_waterways_output_type,
        )
    ]


def bc_wetlands(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=bc_wetlands_provisioner(bbox, run_id)[0],
            style_class="wetlands",
            crs_code=bc_wetlands_crs_code,
            type=bc_wetlands_output_type,
        )
    ]


def bc_ates_zones(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=bc_ates_zones_provisioner(bbox, run_id)[0],
            style_class="bc-ates-zones",
            crs_code=bc_ates_zones_crs_code,
            type=bc_ates_zones_output_type,
        )
    ]


def bc_ates_avpaths(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=bc_ates_av_paths_provisioner(bbox, run_id)[0],
            style_class="bc-ates-av-paths",
            crs_code=bc_ates_av_paths_crs_code,
            type=bc_ates_av_paths_output_type,
        )
    ]


def bc_ates_dec_points(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=bc_ates_dec_points_provisioner(bbox, run_id)[0],
            style_class="bc-ates-dec-points",
            crs_code=bc_ates_dec_points_crs_code,
            type=bc_ates_dec_points_output_type,
        )
    ]


def bc_ates_poi(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=bc_ates_poi_provisioner(bbox, run_id)[0],
            style_class="bc-ates-poi",
            crs_code=bc_ates_poi_crs_code,
            type=bc_ates_poi_output_type,
        )
    ]


def bc_parcels(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=bc_parcels_provisioner(bbox, run_id)[0],
            style_class="parcels",
            crs_code=bc_parcels_crs_code,
            type=bc_parcels_output_type,
        )
    ]


def bc_rec_sites(bbox: BBOX, run_id: str) -> List[ProjectLayer]:
    return [
        ProjectLayer(
            path=bc_rec_sites_provisioner(bbox, run_id)[0],
            style_class="rec-sites",
            crs_code=bc_rec_sites_crs_code,
            type=bc_rec_sites_output_type,
        )
    ]
