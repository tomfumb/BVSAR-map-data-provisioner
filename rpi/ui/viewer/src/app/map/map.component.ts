import { Component } from '@angular/core';
import { HttpClient, HttpResponse } from '@angular/common/http';
import * as l from 'leaflet';
import { environment } from 'src/environments/environment';
import { map } from 'rxjs/operators'

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
export class MapComponent {

  public tilesetSelected: Tileset;
  public tilesets: Tileset[] = [];

  private leafletMap: any;

  constructor(
    private http: HttpClient
  ) {
    this.http.get(`${environment.tile_domain}/tiles/list`).subscribe((response: HttpResponse<object>) => {
      this.tilesets = <Tileset[]><object>response;
      if (this.tilesets.length) {
        this.tilesetSelected = this.tilesets[0];
        this.initMap(this.tilesetSelected);
      }
    });
  }

  public tilesetSelectedChanged(): void {
    this.initMap(this.tilesetSelected);
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
  }
}
