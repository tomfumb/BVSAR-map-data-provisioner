.waterways {
  line-color: #4088f5;
  line-opacity: 0.7;
  [zoom < 14] {
    line-width: 0;
  }
  [zoom >= 14] {
    line-width: 2;
  }
  [zoom >= 16] {
    ::case {
      line-width: 4;
      line-color: #aecaf5;
    }
    ::fill {
      line-width: 2;
      line-color: #4088f5;
    }
  }
}

.wetlands {
  polygon-fill: #4088f5;
  [zoom < 14] {
    polygon-opacity: 0;
  }
  [zoom >= 14] {
    polygon-opacity: 0.4;
  }
}