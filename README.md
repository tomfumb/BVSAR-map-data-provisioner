# BVSAR Map Data Provisioner

Map data provisioning and serving for Bulkley Valley Search and Rescue. Git LFS is currently required to fully clone this repo.

Docuementation is WIP...

- A Dockerised provisioning process builds datasets from publicly-accessible data, locally-maintained data, and provincially-managed data to populate layers that may be useful in various SAR operation types.
- A simple web application and API, designed to run on a Raspberry Pi (tested on 3B+), are provided to serve cached data to clients connected to a WiFi access point managed by the Pi. Documents and configuration files are provided to support configuration of the Pi.

The data provisioning process could be applied to any area within British Columbia and so, in principle, could be used by any BC SAR group to achieve the same result. The output of the provisioning process is a collection of raw .png files that conform to the XYZ tiling system. mb-util may be used to package them into an .mbtiles file for easier management.

## Area Definition
runner-data/areas/areas.gpkg is an empty GeoPackage with the correct schema to define that areas you want to provision. Draw one or more polygons in the areas layer and configure the required attributes (details to follow).

## Local Features
runner-data/local-features/local-features.gpkg is an empty GeoPackage that should be populated with any local trails and shelters you would like included in the provisioned layers (details to follow).

## Provincial Data
Several layer profiles expect data provided by the province of British Columbia and some of these datasets cannot be retrieved automatically by the tool. You must download these datasets manually and store them at the correct location before these layers can be provisioned.

### Resource Roads (used by multiple profiles)
- Navigate to https://maps.gov.bc.ca/ in browser
- Search for and enable All Forest Road Sections - FTEN - Colour Themed
- Export the roads layer with the following selections
    - Geographic Long/Lat (dd)
    - ESRI File Geodatabase
    - None
- Download the .zip archive from the link provided by email
- Extract .zip archive and move the FTEN_ROAD_SECTION_LINES_SVW.gdb directory to the provisioning/data directory
    - You should have a directory provisioning/data/FTEN_ROAD_SECTION_LINES_SVW.gdb

### Rec Sites (used by hunting profile)
- Navigate to https://catalogue.data.gov.bc.ca/dataset/recreation-polygons#edc-pow
- Follow link BC Geographic Warehouse Custom Download -> Access / Download
- Export data with the following selections
    - Geographic Long/Lat (dd)
    - ESRI File Geodatabase
    - None
- Download the .zip archive from the link provided by email
- Extract .zip archive and move the FTEN_RECREATION_POLY_SVW.gdb directory to the provisioning/data directory
    - You should have a directory provisioning/data/FTEN_RECREATION_POLY_SVW.gdb

### Parcel Fabric
- Navigate to https://catalogue.data.gov.bc.ca/dataset/parcelmap-bc-parcel-fabric
- Follow first link Parcel Fabric File Geodatabase (NAD83 / BC Albers) -> Access / Download and wait for .zip archive to download
- Extract .zip archive and move the pmbc_parcel_fabric_poly_svw.gdb directory to the provisioning/data directory
    - You should have a directory provisioning/data/pmbc_parcel_fabric_poly_svw.gdb