import { Component, OnDestroy, OnInit } from '@angular/core';
import { HttpClient, HttpResponse } from '@angular/common/http';
import * as l from 'leaflet';
import { environment } from 'src/environments/environment';
import { map } from 'rxjs/operators'
import { forkJoin, Observable, Observer } from 'rxjs';
import { CopyService } from '../copy.service';

interface Tileset {
  name: string;
  zoom_min: number;
  zoom_max: number;
}

interface ExportInfo {
  z: number;
  x_tiles: number;
  y_tiles: number;
  sample: string;
  permitted: boolean;
}

interface MapState {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  zoom: number;
}

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.less']
})
export class MapComponent implements OnInit, OnDestroy {

  public tilesetSelected: Tileset;
  public tilesets: Tileset[] = [];
  public tileUrls: {[index: string]: string} = {};

  public exportInProgress: boolean = false;
  public exportInfos: ExportInfo[] = [];

  private leafletMap: any;
  private initObserver: Observer<void>;

  constructor(
    private http: HttpClient,
    private copyService: CopyService
  ) {
    forkJoin([
      this.http.get<Tileset[]>(`${environment.tile_domain}/tile/list`),
      new Observable(observer => {
        this.initObserver = observer;
      })
    ]).subscribe(results => {
      this.tilesets = results[0];
      if (this.tilesets.length) {
        this.tilesetSelected = this.tilesets[0];
        this.initMap(this.tilesetSelected);
      }
    });
  }
  
  public ngOnInit(): void {
    this.initObserver.next(null);
    this.initObserver.complete();
  }

  public ngOnDestroy(): void {
    if (this.leafletMap) {
      this.leafletMap.off();
      this.leafletMap.remove();
    }
  }

  public tilesetSelectedChanged(): void {
    this.endExport();
    this.initMap(this.tilesetSelected);
  }

  public keepOriginalOrder(a: any, _: any): string {
    return a.key;
  }

  public copyUrl(url: string): void {
    this.copyService.copyText(url);
  }

  public initiateExport(): void {
    if (!this.leafletMap) {
      console.error("Attempt to export before map is ready");
      return;
    }
    this.exportInProgress = true;
    this.updateExportOptions();
    this.leafletMap.on("moveend", () => {
      this.updateExportOptions();
   });
  }

  public endExport(): void {
    this.exportInProgress = false;
  }

  public requestExport(zoom: number): void {
    const mapState = this.getMapState();
    const exportUrl = `${environment.tile_domain}/export/pdf/${zoom}/${mapState.minX}/${mapState.minY}/${mapState.maxX}/${mapState.maxY}/${this.tilesetSelected.name}`
    window.open(exportUrl, "PDF Export");
    this.endExport();
  }

  private updateExportOptions(): void {
    this.exportInfos = [];
    const mapState = this.getMapState();
    const minZoom = Math.max(mapState.zoom, this.tilesetSelected.zoom_min);
    const infoRequestObservables = [];
    for(let i = minZoom; i <= this.tilesetSelected.zoom_max; i++) {
      infoRequestObservables.push(this.http.get(`${environment.tile_domain}/export/info/${i}/${mapState.minX}/${mapState.minY}/${mapState.maxX}/${mapState.maxY}/${this.tilesetSelected.name}`));
    }
    forkJoin(infoRequestObservables).subscribe((results: HttpResponse<ExportInfo>[]) => {
      this.exportInfos = (<any>results).filter((exportInfo: ExportInfo) => exportInfo.permitted);
    });
  }

  private getMapState(): MapState {
    const [minX, minY, maxX, maxY] = this.leafletMap.getBounds().toBBoxString().split(",")
    return {
      minX: minX,
      minY: minY,
      maxX: maxX,
      maxY: maxY,
      zoom: this.leafletMap.getZoom()
    };
  }

  private initMap(tileset: Tileset): void {
    const rootPath = `${environment.tile_domain}/tiles/files/${this.tilesetSelected.name}`;
    this.http.get(`${rootPath}/coverage.geojson`).pipe(map((response: HttpResponse<object>) => {
      return response;
    })).subscribe(geojson => {
      const zoomMin = tileset.zoom_min;
      const zoomMax = tileset.zoom_max;
      let initialBounds = l.geoJson(geojson).getBounds();
      if (this.leafletMap) {
        // TODO: determine if the current bounds and new bounds intersect and share the same zoom levels. If they do, set current as new
        this.leafletMap.off();
        this.leafletMap.remove();
      }
      this.leafletMap = l.map("map");
      l.tileLayer(`${rootPath}/{z}/{x}/{y}.png`, {
        minZoom: zoomMin,
        maxZoom: zoomMax
      }).addTo(this.leafletMap);
      this.leafletMap.fitBounds(initialBounds);
    });
    this.tileUrls = this.buildTileUrls();
  }

  private buildTileUrls(): {[index: string]: string} {
    const baseUrl = `${window.location.protocol}//${window.location.host}/tiles/files/${this.tilesetSelected.name}/`
    return {
      "GIS Kit": `${baseUrl}#Z#/#X#/#Y#.png`,
      "Touch GIS": `${baseUrl}{z}/{x}/{y}.png`,
      "QGIS": `${baseUrl}{z}/{x}/{y}.png`
    };
  }
}
