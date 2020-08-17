import { Component, AfterViewInit } from '@angular/core';
import { HttpClient, HttpResponse } from '@angular/common/http';
import * as l from 'leaflet';
import { forkJoin, of, Observable, Observer } from 'rxjs';
import { map, catchError } from 'rxjs/operators'
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.less']
})
export class MapComponent implements AfterViewInit {

  private readonly MAX_POSSIBLE_ZOOM = 22;

  private componentInitObserver: Observer<void>;
  private componentInitObservable: Observable<void> = Observable.create(observer => {
    this.componentInitObserver = observer;
  });

  constructor(
    http: HttpClient
  ) {
    // TODO: hack around lack of query params because Angular app is not confiured for routing
    const rootPath = `${environment.tile_domain}/${new URLSearchParams(window.location.search).get("path")}`;
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
      })),
      this.componentInitObservable
    ]).subscribe(initOutcomes => {
      this.initMap(initOutcomes[0][0], initOutcomes[0][1], initOutcomes[1], rootPath);
    });
  }

  public ngAfterViewInit(): void {
    this.componentInitObserver.next(null);
    this.componentInitObserver.complete();
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
