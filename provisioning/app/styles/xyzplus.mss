.waterways {
  line-color: #0000ff;
  line-opacity: 0.7;
  [zoom < 12] {
    line-width: 0;
  }
  [zoom = 12] {
    line-width: 0.25;
  }
  [zoom >= 13][zoom <= 15] {
    line-width: 0.5;
  }
  [zoom > 15] {
    line-width: 1;
  }
}