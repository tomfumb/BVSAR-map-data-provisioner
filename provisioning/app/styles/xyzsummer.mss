.waterways {
  line-color: #0E97D3;
  line-opacity: 0.7;
  [zoom < 14] {
    line-width: 0;
  }
  [zoom = 14][zoom = 15] {
    line-width: 1;
  }
  [zoom = 16] {
    line-width: 2;
  }
  [zoom = 17] {
    line-width: 3;
  }
}

.wetlands {
  polygon-fill: #0E97D3;
  [zoom < 14] {
    polygon-opacity: 0;
  }
  [zoom >= 14] {
    polygon-opacity: 0.6;
  }
}