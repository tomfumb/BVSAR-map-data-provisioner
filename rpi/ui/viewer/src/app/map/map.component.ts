import { Component, OnDestroy, OnInit } from '@angular/core';
import { HttpClient, HttpResponse } from '@angular/common/http';
import * as l from 'leaflet';
import { environment } from 'src/environments/environment';
import { map } from 'rxjs/operators'
import { forkJoin, Observable, Observer } from 'rxjs';
import { MatDialog } from '@angular/material/dialog';
import { TileUrlsComponent } from './tile-urls/tile-urls.component';
import { PdfExportComponent } from './pdf-export/pdf-export.component';
import { Tileset } from './tileset';
import { ReCentreComponent } from './re-centre/re-centre.component';
import { CoordinateService } from '../coordinate.service';
import { ActivatedRoute } from '@angular/router';
import { BenchComponent } from './mode-providers/bench/bench.component';

enum Modes {
  bench = "bench"
}

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.less']
})
export class MapComponent implements OnInit, OnDestroy {

  private tilesets: Tileset[] = [];
  private tilesetSelected: Tileset;
  private leafletMap: l.map;
  private initObserver: Observer<void>;
  private dataModifiedLabel: l.Control;
  private mapCentreLabel: l.Control;

  constructor(
    private http: HttpClient,
    private dialog: MatDialog,
    private coordinateService: CoordinateService,
    private route: ActivatedRoute,
  ) {
    forkJoin([
      this.http.get<Tileset[]>(`${environment.tile_domain}/tile/list`),
      new Observable(observer => {
        this.initObserver = observer;
      })
    ]).subscribe(results => {
      this.tilesets = results[0];
      if (this.tilesets.length) {
        let initialTileset: Tileset = null;
        if (this.route.snapshot.params.hasOwnProperty("layer")) {
          const matchingTilesets = this.tilesets.filter(tileset => {
            return tileset.name === this.route.snapshot.params.layer;
          });
          if (matchingTilesets.length === 1) {
            initialTileset = matchingTilesets[0];
          }
        } else {
          // if there is a dataset that appears suitable for the time of year, select it by default
          const season = [3,4,5,6,7,8,9].indexOf((new Date().getMonth())) > -1 ? "summer" : "winter";
          const seasonRegex = new RegExp(`${season}`, "i");
          const seasonTilesets = this.tilesets.filter(tileset => {
            return !!tileset.name.match(seasonRegex);
          });
          if (seasonTilesets.length > 0) {
            initialTileset = seasonTilesets[0];
          }
        }
        if (initialTileset) {
          this.tilesetSelected = initialTileset;
        } else {
          console.log(`Failed to select preferred tileset`);
          this.tilesetSelected = this.tilesets[0];
        }
        this.route.queryParams.subscribe(() => {
          if (this.leafletMap) {
            this.leafletMap.off();
            this.leafletMap.remove();
          }
          this.initMap();
        });
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

  public get hasTilesets(): boolean {
    return this.tilesets.length > 0;
  }

  private get useSupertile() {
    return this.route.snapshot.queryParams.hasOwnProperty("super") ? 1 : 0;
  }

  private initMap(): void {
    const generateRandInt = function() {
      return Math.floor( Math.random() * 200000 ) + 1;
    };
    window.setTimeout(() => {
      const tileLayers = this.tilesets.reduce((accumulator, currentValue) => {
        accumulator[currentValue.name] = l.tileLayer(`${environment.tile_domain}/tile/file/${currentValue.name}/{z}/{x}/{y}.png?supertile={supertile}&cachebust={randInt}`, {
          supertile: this.useSupertile,
          randInt: generateRandInt,
          minZoom: currentValue.zoom_min,
          maxZoom: currentValue.zoom_max - (this.useSupertile === 1 ? 1 : 0)
        })
        return accumulator;
      }, {});
      this.leafletMap = l.map("map");
      this.leafletMap.on("load", event => {
        this.mapLoaded();
      });
      this.leafletMap.on("baselayerchange", event => {
        this.tilesetSelected = this.tilesets.find(tileset => {
          return tileset.name === event.name;
        });
        this.tilesetSelectedChanged(true);
      });
      this.leafletMap.on("moveend", _ => {
        if (this.mapCentreLabel) {
          this.mapCentreLabel.getContainer().innerHTML = this.getCentreText();
        }
      });
      tileLayers[this.tilesetSelected.name].addTo(this.leafletMap);
      l.control.layers(tileLayers).addTo(this.leafletMap);
      this.tilesetSelectedChanged(false);
      new (this.leafletModalOpener("Export", PdfExportComponent, () => {
        return {
          tileset: this.tilesetSelected,
          map: this.leafletMap
        };
      }))({ position: "bottomright" }).addTo(this.leafletMap);
      new (this.leafletModalOpener("Re-Centre", ReCentreComponent, () => {
        return {
          map: this.leafletMap
        };
      }))({ position: "bottomright" }).addTo(this.leafletMap);
      new (this.leafletModalOpener("Get URLs", TileUrlsComponent, () => {
        return {
          tileset: this.tilesetSelected
        };
      }))({ position: "bottomright" }).addTo(this.leafletMap);
      const initialText = this.getModifiedText();
      this.dataModifiedLabel = new (l.Control.extend({
        onAdd: function() {
          const lastModifiedLabel = l.DomUtil.create("div");
          lastModifiedLabel.innerHTML = initialText;
          lastModifiedLabel.id = "last-modified-label";
          lastModifiedLabel.className = "map-state-label-text";
          return lastModifiedLabel;
        }
      }))({ position: "bottomleft" });
      this.dataModifiedLabel.addTo(this.leafletMap)
      this.mapCentreLabel = new (l.Control.extend({
        onAdd: function() {
          const mapCentreLabel = l.DomUtil.create("div");
          mapCentreLabel.innerHTML = "...";
          mapCentreLabel.id = "map-centre-label";
          mapCentreLabel.className = "map-state-label-text";
          return mapCentreLabel;
        }
      }))({ position: "bottomleft" });
      this.mapCentreLabel.addTo(this.leafletMap)

      // locate will work on localhost but not via IP address / domain without HTTPS
      // HTTPS unavailable / impractical with pi device over the long term
      // new (l.Control.extend({
      //   onAdd: function(map: l.map) {
      //       const btn = l.DomUtil.create("button");
      //       btn.innerHTML = `<img src="assets/locate.png" width="32px" height="34px" />`;
      //       btn.onclick = function() { alert(`fish, ${map}`); map.locate({ setView: true }); };
      //       btn.className = "clickable";
      //       btn.type="button";
      //       return btn;
      //   }
      // }))({ position: "topright" }).addTo(this.leafletMap);
    });
  }

  private leafletModalOpener(label: string, componentType: any, dataProvider: () => any): l.Control {
    return l.Control.extend({
      onAdd: function() {
          const btn = l.DomUtil.create("button");
          btn.innerHTML = label;
          btn.onclick = this.openModal;
          btn.className="primary-button map-action-button";
          btn.type="button";
          return btn;
      },
      openModal: () => {
        this.dialog.open(componentType, {
          data: dataProvider(),
          width: componentType.WIDTH,
          panelClass: componentType.PANEL_CLASS
        });
      }
    });
  }

  private tilesetSelectedChanged(respectCurrentBounds: boolean): void {
    if (this.dataModifiedLabel) {
      this.dataModifiedLabel.getContainer().innerHTML = this.getModifiedText();
    }
    const geojson = JSON.parse(this.tilesetSelected.geojson);
    let newBounds = l.geoJson(geojson).getBounds();
    if (respectCurrentBounds) {
      const currentBounds = this.leafletMap.getBounds();
      if (respectCurrentBounds && newBounds.intersects(currentBounds)) {
        newBounds = currentBounds
      }
    }
    this.leafletMap.fitBounds(newBounds);
  }

  private getModifiedText(): string {
    const modifiedDate = new Date(this.tilesetSelected.last_modified);
    return `${this.tilesetSelected.name} last updated ${modifiedDate.getFullYear()}/${("0" + (modifiedDate.getMonth() + 1)).slice(-2)}/${("0" + modifiedDate.getDate()).slice(-2)}`;
  }

  private getCentreText(): string {
    const latLng = this.leafletMap.getCenter();
    return `Centre: ${this.coordinateService.roundTo(latLng.lat, CoordinateService.MAX_PRECISION_DD)}, ${this.coordinateService.roundTo(latLng.lng, CoordinateService.MAX_PRECISION_DD)}`
  }

  private mapLoaded(): void {
    if (this.route.snapshot.params.mode == undefined) {
      return;
    }
    const mode = this.route.snapshot.params.mode as Modes;
    switch (mode) {
      case Modes.bench:
        this.dialog.open(BenchComponent, {
          data: {
            map: this.leafletMap,
            tileset: Object.assign({}, this.tilesetSelected, {
              zoom_max: this.tilesetSelected.zoom_max - (this.useSupertile === 1 ? 1 : 0)
            })
          },
          width: BenchComponent.WIDTH,
          panelClass: BenchComponent.PANEL_CLASS,
          disableClose: true
        });
        break;
      default:
        console.error(`Unknown mode requested: ${mode}`)
    }
  }
}
