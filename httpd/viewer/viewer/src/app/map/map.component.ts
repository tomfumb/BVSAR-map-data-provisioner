import { Component } from '@angular/core';
import { HttpClient, HttpResponse } from '@angular/common/http';
import * as l from 'leaflet';
import { forkJoin, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators'
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.less']
})
export class MapComponent {

  public directoryList: string[] = [];
  public directorySelected: string;
  public errorMessage: string;

  private readonly MAX_POSSIBLE_ZOOM = 22;

  constructor(
    http: HttpClient
  ) {
    http.get(`${environment.tile_domain}/`, {
      responseType: "text"
    }).subscribe((response: string) => {
      this.directoryList = response.match(/<a href=".+">\s+.+<\/a>/gi).map(link => {
        return link.replace(/<a href=".+">\s+/, "").replace(/\/?<\/a>/, "")
      }).filter(link => {
        return !link.match(/.DS_Store|viewer/i);
      });
      if (this.directoryList.length === 0) {
        this.errorMessage = "No tiles. Tile generator must be run"
      } else {
        this.directorySelected = this.directoryList[0];
        const rootPath = `${environment.tile_domain}/${this.directorySelected}`;
        forkJoin([
          forkJoin(
            Array(this.MAX_POSSIBLE_ZOOM).fill(undefined).map(
              (_: undefined, i: number) => {
                return http.head(`${rootPath}/${i}/`).pipe(map(_ => true)).pipe(catchError(_ => of(false)))
              }
            )
          ).pipe(map(result => {
            const validZooms = result.map((exists: boolean, idx: number) => {
              return exists ? idx : undefined;
            }).filter(entry => entry !== undefined);
            return [Math.min(...validZooms), Math.max(...validZooms)];
          })),
          http.get(`${rootPath}/coverage.geojson`).pipe(map((response: HttpResponse<object>) => {
            return response;
          }))
        ]).subscribe(initOutcomes => {
          this.initMap(initOutcomes[0][0], initOutcomes[0][1], initOutcomes[1], rootPath);
        });
      }
    });
  }

  get directorySelectedAccess() {
    return this.directorySelected;
  }

  set directorySelectedAccess(value) {
    this.directorySelected = value;
    console.warn("Not yet implemented - switch to different directory");
  }

  private initMap(minZoom: number, maxZoom: number, geojson: object, rootPath: string): void {
    const coverage = l.geoJson(geojson, {
      style: {
        "color": "#ff0000",
        "weight": 2,
        "opacity": 1,
        "fillOpacity": 0
      }
    });
    const bounds = coverage.getBounds();
    const map = l.map("map", {
      center: bounds.getCenter(),
      zoom: minZoom,
      maxBounds: bounds
    });
    l.tileLayer(`${rootPath}/{z}/{x}/{y}.png`, {
      minZoom: minZoom,
      maxZoom: maxZoom
    }).addTo(map);
    coverage.addTo(map);
    map.fitBounds(bounds);
  }
}
