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
  [zoom = 12][zoom = 13] {
    line-width:1;
  }
  [zoom = 14][zoom = 15] {
    line-width: 2;
  }
  [zoom > 15] {
    line-width: 3;
  }
}

.bc-resource-roads-label {
  line-width:0;
  [zoom >= 14] {
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
  [zoom >= 14] {
    text-dy:5;
    text-face-name:'DejaVu Sans Book';
    text-halo-radius:2;
    text-avoid-edges:true;
    text-placement:line;
  }
}

.trails {
  [zoom >= 14] {
    text-name:[name];
  }
}

.shelters {
  [zoom >= 12] {
    marker-file: url(/icons/cabin.png);
    marker-width:16;
    marker-height:16;
  }
  [zoom = 14] {
    marker-width:20;
    marker-height:20;
  }
  [zoom = 15] {
    marker-width:24;
    marker-height:24;
  }
  [zoom >= 16] {
    marker-width:28;
    marker-height:28;
  }
}