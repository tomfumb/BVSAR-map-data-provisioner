import { Component, OnInit } from '@angular/core';
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

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.less']
})
export class MapComponent implements OnInit {

  public tilesetSelected: Tileset;
  public tilesets: Tileset[] = [];
  public tileUrls: {[index: string]: string} = {};

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

  public tilesetSelectedChanged(): void {
    this.initMap(this.tilesetSelected);
  }

  public keepOriginalOrder(a: any, _: any): string {
    return a.key;
  }

  public copyUrl(url: string): void {
    this.copyService.copyText(url);
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
