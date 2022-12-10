.bc-ates-zones [zoom >= 11] {
  [Name = "Simple"] {
    polygon-fill: #70BF44;
    polygon-opacity: 0.6;
  }
  [Name = "Challenging"] {
    polygon-fill: #5C75B8;
    polygon-opacity: 0.6;
  }
  [Name = "Complex"] {
    polygon-fill: #595959;
    polygon-opacity: 0.8;
  }
}

.bc-ates-av-paths [zoom >= 11] {
  line-width: 1;
  line-color: #ff0000;
  [zoom >= 15] {
    line-width: 2;
  }
}

.bc-ates-dec-points {
  [zoom >= 13] {
    marker-file: url(/icons/decision-point.png);
    marker-width:16;
    marker-height:16;
  }
  [zoom > 14] {
    marker-file: url(/icons/decision-point.png);
    marker-width: 24;
    marker-height: 24;
  }
}

.bc-ates-poi {
  [zoom >= 13] {
    marker-file: url(/icons/destination.png);
    marker-width:16;
    marker-height:16;
  }
  [zoom > 14] {
    marker-file: url(/icons/destination.png);
    marker-width: 24;
    marker-height: 24;
  }
}
