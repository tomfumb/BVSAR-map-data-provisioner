import { Component, OnDestroy, OnInit } from '@angular/core';
import { HttpClient, HttpResponse } from '@angular/common/http';
import * as l from 'leaflet';
import { environment } from 'src/environments/environment';
import { map } from 'rxjs/operators'
import { forkJoin, Observable, Observer } from 'rxjs';
import { CopyService } from '../copy.service';
import { TouchService } from '../touch.service';

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

  public tileUrls: {[index: string]: string} = {};

  public exportInProgress: boolean = false;
  public exportInfos: ExportInfo[] = [];

  private tilesets: Tileset[] = [];
  private tilesetSelected: Tileset;
  private leafletMap: any;
  private initObserver: Observer<void>;
  
  private updateExportOptionsTimeout: number = null;
  private readonly updateExportOptionsAfterBind = () => { this.updateExportOptionsAfter(500); };


  constructor(
    private http: HttpClient,
    private copyService: CopyService,
    private touchService: TouchService
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
        this.initMap();
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

  public keepOriginalOrder(a: any, _: any): string {
    return a.key;
  }

  public copyUrl(url: string): void {
    this.copyService.copyText(url);
  }

  public get hasTilesets(): boolean {
    return this.tilesets.length > 0;
  }

  public initiateExport(): void {
    if (!this.leafletMap) {
      console.error("Attempt to export before map is ready");
      return;
    }
    this.exportInProgress = true;
    this.updateExportOptions();
    this.leafletMap.on("moveend", this.updateExportOptionsAfterBind);
    this.leafletMap.on("resize", this.updateExportOptionsAfterBind);
  }

  public endExport(): void {
    this.exportInProgress = false;
    this.leafletMap.off("moveend", this.updateExportOptionsAfterBind);
    this.leafletMap.off("resize", this.updateExportOptionsAfterBind);
  }

  public requestExport(zoom: number): void {
    const mapState = this.getMapState();
    const exportUrl = `${environment.tile_domain}/export/pdf/${zoom}/${mapState.minX}/${mapState.minY}/${mapState.maxX}/${mapState.maxY}/${this.tilesetSelected.name}`
    window.open(exportUrl, "PDF Export");
    this.endExport();
  }

  private updateExportOptions(): void {
    if (this.exportInProgress) {
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
  }

  private updateExportOptionsAfter(delay: number): void {
    if (this.updateExportOptionsTimeout !== null) {
      window.clearTimeout(this.updateExportOptionsTimeout);
    }
    this.updateExportOptionsTimeout = window.setTimeout(() => {
      this.updateExportOptions();
      this.updateExportOptionsTimeout = null;
    }, delay);
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

  private initMap(): void {
    window.setTimeout(() => {
      const tileLayers = this.tilesets.reduce((accumulator, currentValue) => {
        accumulator[currentValue.name] = l.tileLayer(`${environment.tile_domain}/tiles/files/${currentValue.name}/{z}/{x}/{y}.png`, {
          minZoom: currentValue.zoom_min,
          maxZoom: currentValue.zoom_max
        })
        return accumulator;
      }, {});
      this.leafletMap = l.map("map", {dragging: !this.touchService.touchEnabled});
      this.leafletMap.on("baselayerchange", event => {
        this.tilesetSelected = this.tilesets.find(tileset => {
          return tileset.name === event.name;
        });
        this.tilesetSelectedChanged(true);
      });
      tileLayers[this.tilesetSelected.name].addTo(this.leafletMap);
      l.control.layers(tileLayers).addTo(this.leafletMap);
      this.tilesetSelectedChanged(false);
    });
  }

  private tilesetSelectedChanged(respectCurrentBounds: boolean): void {
    this.http.get(`${environment.tile_domain}/tiles/files/${this.tilesetSelected.name}/coverage.geojson`).pipe(map((response: HttpResponse<object>) => {
      return response;
    })).subscribe(geojson => {
      let newBounds = l.geoJson(geojson).getBounds();
      if (respectCurrentBounds) {
        const currentBounds = this.leafletMap.getBounds();
        if (respectCurrentBounds && newBounds.intersects(currentBounds)) {
          newBounds = currentBounds
        }
      }
      this.leafletMap.fitBounds(newBounds);
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
