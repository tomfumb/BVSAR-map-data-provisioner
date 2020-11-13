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

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.less']
})
export class MapComponent implements OnInit, OnDestroy {

  private tilesets: Tileset[] = [];
  private tilesetSelected: Tileset;
  private leafletMap: any;
  private initObserver: Observer<void>;
  private dataModifiedLabel: l.Control;

  constructor(
    private http: HttpClient,
    private dialog: MatDialog
  ) {
    forkJoin([
      this.http.get<Tileset[]>(`${environment.tile_domain}/tile/list`),
      new Observable(observer => {
        this.initObserver = observer;
      })
    ]).subscribe(results => {
      this.tilesets = results[0];
      if (this.tilesets.length) {
        try {
          // if there is a dataset that appears suitable for the time of year, select it by default
          const season = [3,4,5,6,7,8,9].indexOf((new Date().getMonth())) > -1 ? "summer" : "winter";
          const seasonRegex = new RegExp(`${season}`, "i");
          const seasonTilesets = this.tilesets.filter(tileset => {
            return !!tileset.name.match(seasonRegex);
          });
          if (seasonTilesets.length > 0) {
            this.tilesetSelected = seasonTilesets[0];
          }
        } catch (ex) {
          console.log(`Failed to select a seasonal tileset: ${ex}`);
        } finally {
          if (!this.tilesetSelected) {
            this.tilesetSelected = this.tilesets[0];
          }
        }
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

  public get hasTilesets(): boolean {
    return this.tilesets.length > 0;
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
      this.leafletMap = l.map("map");
      this.leafletMap.on("baselayerchange", event => {
        this.tilesetSelected = this.tilesets.find(tileset => {
          return tileset.name === event.name;
        });
        this.tilesetSelectedChanged(true);
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
      new (this.leafletModalOpener("URLs", TileUrlsComponent, () => {
        return {
          tilesetName: this.tilesetSelected.name
        };
      }))({ position: "bottomright" }).addTo(this.leafletMap);
      const initialText = this.getModifiedText();
      this.dataModifiedLabel = new (l.Control.extend({
        onAdd: function() {
          const lastModifiedLabel = l.DomUtil.create("div");
          lastModifiedLabel.innerHTML = initialText;
          lastModifiedLabel.id = "last-modified-label";
          return lastModifiedLabel;
        }
      }))({ position: "bottomleft" });
      this.dataModifiedLabel.addTo(this.leafletMap)
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
  }

  private getModifiedText(): string {
    const modifiedDate = new Date(this.tilesetSelected.last_modified);
    return `${this.tilesetSelected.name} last updated ${modifiedDate.getFullYear()}/${("0" + (modifiedDate.getMonth() + 1)).slice(-2)}/${("0" + modifiedDate.getDate()).slice(-2)}`;
  }
}
