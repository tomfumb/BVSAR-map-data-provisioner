.bc-resource-roads,.trails {
  [zoom < 12] {
    line-width:0;
  }
  [zoom >= 12] {
    line-width:1;
  }
}

.bc-resource-roads {
  line-color:#CD5406;
  [zoom = 13] {
    line-width: 2;
  }
  [zoom = 14] {
    ::case {
      line-width: 3;
      line-color: #e3ad8c;
    }
    ::fill {
      line-width: 1;
      line-color:#CD5406;
    }
  }
  [zoom >= 15] {
    ::case {
      line-width: 4;
      line-color: #e3ad8c;
    }
    ::fill {
      line-width: 2;
      line-color:#CD5406;
    }
  }
}

.trails {
  line-color:#960BA4;
  [zoom = 13] {
    line-width: 2;
  }
  [zoom = 14] {
    ::case {
      line-width: 3;
      line-color: #cd92d2;
    }
    ::fill {
      line-width: 1;
      line-color: #960BA4;
    }
  }
  [zoom >= 15] {
    ::case {
      line-width: 4;
      line-color: #cd92d2;
    }
    ::fill {
      line-width: 2;
      line-color: #960BA4;
    }
  }
}

.bc-resource-roads-label {
  line-width:0;
  [zoom >= 14] {
    text-name:[ROAD_SEC_1];
    [LIFE_CYCLE = "ACTIVE"] {
      text-fill:"#000";  
    }
    [LIFE_CYCLE = "RETIRED"] {
      text-fill:"#626161";
    }
  }
}

.bc-resource-roads-label,.trails-label {
  [zoom >= 14] {
    text-dy:5;
    text-face-name:'DejaVu Sans Book';
    text-halo-radius:2;
    text-avoid-edges:true;
    text-placement:line;
  }
}

.trails-label {
  line-width:0;
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
