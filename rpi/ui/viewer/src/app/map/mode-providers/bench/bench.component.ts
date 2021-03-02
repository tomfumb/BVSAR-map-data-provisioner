import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import * as l from 'leaflet';
import { Tileset } from '../../tileset';

interface Parameters {
  map: l.map;
  tileset: Tileset;
}

@Component({
  selector: 'app-bench',
  templateUrl: './bench.component.html',
  styleUrls: ['./bench.component.less']
})
export class BenchComponent implements OnInit {

  public static readonly WIDTH = "80%";
  public static readonly PANEL_CLASS = "common-modal-panel";
  
  public pendingRequests: number = 0;
  public totalRequests: number = 0;
  public runningAverage: number = 0;
  public points: l.latLng[] = [];

  private readonly ITERATION_PER_COVERAGE = 100;

  private handlers: {[index: string]: () => void};
  private map: l.Map;
  private baseLayer: l.Layer;
  private tileset: Tileset;
  private timingInitiated: boolean = false;
  private timings = [];
  private nextZoom: number;

  constructor(
    private dialogRef: MatDialogRef<BenchComponent>,
    @Inject(MAT_DIALOG_DATA) public data: Parameters
  ) {
    this.map = data.map;
    this.baseLayer = data.map._layers[Object.keys(data.map._layers)[0]];
    this.tileset = data.tileset;
    this.handlers = {
      "load": this.mapLoad.bind(this),
      "tileloadstart": this.loadStart.bind(this),
      "tileload": this.loadEnd.bind(this),
      "tileerror": this.loadError.bind(this)
    };
  }

  public ngOnInit(): void {
    Object.keys(this.handlers).forEach(eventName =>  {
      this.baseLayer.on(eventName, this.handlers[eventName]);
    });
  }

  public ngOnDestroy(): void {
    // possible race condition to address - what happens if destroyed before baseLayer's load event fires (unlikely)
    Object.keys(this.handlers).forEach(eventName =>  {
      this.baseLayer.off(eventName, this.handlers[eventName]);
    });
  }

  private mapLoad(): void {
    if (!this.timingInitiated) {
      this.timingInitiated = true;
      this.initiate();
    } else {
      this.timings[this.timings.length - 1].push(Date.now());
      this.updateRunningAverage();
      window.setTimeout(() => {
        this.nextPoint();
      });
    }
  }

  private loadStart(): void {
    if (this.timingInitiated) {
      this.totalRequests++;
    }
    this.pendingRequests++;
  }

  private loadEnd(): void {
    this.pendingRequests--;
  }

  private loadError(e): void {
    console.log(`Tile error: ${e}`);
    this.loadEnd();
  }

  private initiate(): void {
    this.pendingRequests = 0;
    this.nextZoom = this.tileset.zoom_max;
    const coverage = JSON.parse(this.tileset.geojson);
    coverage.features.forEach(feature => {
      const bounds = l.geoJson(feature).getBounds();
      const xDiff = bounds.getEast() - bounds.getWest();
      const yDiff = bounds.getNorth() - bounds.getSouth();
      for (let i = 0; i < this.ITERATION_PER_COVERAGE; i++) {
        const x = bounds.getWest() + xDiff * Math.random();
        const y = bounds.getSouth() + yDiff * Math.random();
        this.points.push(l.latLng(y, x));
      }
    });
    this.shuffleArray(this.points);
    this.nextPoint();
  }

  private nextPoint(): void {
    this.timings.push([Date.now()]);
    if (this.points.length > 0) {
      const nextPoint = this.points.pop()
      this.map.setView(nextPoint, this.nextZoom);
      if (this.nextZoom === this.tileset.zoom_min) {
        this.nextZoom = this.tileset.zoom_max;
      } else {
        this.nextZoom--;
      }
    }
  }

  private updateRunningAverage(): void {
    const totalTime = this.timings.map(ends => {
      return ends[1] - ends[0];
    }).reduce((total, each) => {
      return total + each;
    });
    this.runningAverage = totalTime / this.totalRequests;
  }

  /* 
    https://stackoverflow.com/a/12646864/519575
    Randomize array in-place using Durstenfeld shuffle algorithm
  */
  private shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
  }
}
