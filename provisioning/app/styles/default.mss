Map { background-color: #fff }

.bc-hillshade [zoom <= 15] {
  raster-opacity:0.3;
}

.bc-resource-roads {
  line-color:#CD5406;
}

.trails {
  line-color:#960BA4;
}

.bc-resource-roads,.trails {
  [zoom < 12] {
    line-width:0;
  }
  [zoom = 12] {
    line-width:0.5;
  }
  [zoom = 13] {
    line-width: 1;
  }
  [zoom = 14] {
    line-width: 1.5;
  }
  [zoom >= 15] {
    line-width: 2;
  }
}

.bc-resource-roads-label {
  line-width:0;
  [zoom >= 15] {
    text-name:[RD_SECT_NM];
    [LIFE_ST_CD = "ACTIVE"] {
      text-fill:"#000";  
    }
    [LIFE_ST_CD = "RETIRED"] {
      text-fill:"#626161";
    }
  }
}

.bc-resource-roads-label,.trails {
  [zoom >= 15] {
    text-dy:5;
    text-face-name:'DejaVu Sans Book';
    text-halo-radius:2;
    text-avoid-edges:true;
    text-placement:line;
  }
}

.trails {
  [zoom >= 15] {
    text-name:[name];
  }
}

.shelters {
  marker-fill:#f45;
  marker-line-color:#813;
  marker-allow-overlap:true;
  marker-ignore-placement:true;
  [zoom < 12] {
    marker-width: 0;
  }
  [zoom >= 12][zoom < 14] {
    marker-width:4;
  }
  [zoom = 14] {
    marker-width:6;
  }
  [zoom >= 15] {
    marker-width:8;
  }
}

.canvec-10000000 [zoom = 6] { raster-opacity: 1; }
.canvec-4000000 [zoom = 7] { raster-opacity: 1; }
.canvec-2000000 [zoom = 8] { raster-opacity: 1; }
.canvec-1000000 [zoom = 9] { raster-opacity: 1; }
.canvec-500000 [zoom = 10] { raster-opacity: 1; }
.canvec-250000 [zoom = 11] { raster-opacity: 1; }
.canvec-150000 [zoom = 12] { raster-opacity: 1; }
.canvec-70000 [zoom = 13] { raster-opacity: 1; }
.bc-topo-20000[zoom = 14] { raster-opacity: 1; }
.bc-topo-20000[zoom = 15] { raster-opacity: 1; }