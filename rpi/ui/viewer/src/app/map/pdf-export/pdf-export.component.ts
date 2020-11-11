import { HttpClient, HttpResponse } from '@angular/common/http';
import { Component, OnInit, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from  '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import * as l from 'leaflet';
import { forkJoin } from 'rxjs';
import { environment } from 'src/environments/environment';
import { Tileset } from '../tileset';

interface ExportInfoCommon {
  is_placeholder: boolean;
}

interface ExportInfo extends ExportInfoCommon {
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

interface Parameters {
  map: l.map;
  tileset: Tileset;
}

@Component({
  selector: 'app-pdf-export',
  templateUrl: './pdf-export.component.html',
  styleUrls: ['./pdf-export.component.less']
})
export class PdfExportComponent implements OnInit {

  public static readonly WIDTH = "80%";
  public static readonly PANEL_CLASS = "common-modal-panel";

  public exportInfos: ExportInfoCommon[] = [];
  public exportInProgress: boolean = false;

  private map: l.map;
  private tileset: Tileset;
  private updateExportOptionsTimeout: number = null;
  private readonly updateExportOptionsAfterBind = () => { this.updateExportOptionsAfter(500); };

  constructor(
    private dialogRef: MatDialogRef<PdfExportComponent>,
    private snackBar: MatSnackBar,
    private http: HttpClient,
    @Inject(MAT_DIALOG_DATA) public data: Parameters
  ) {
    this.map = data.map;
    this.tileset = data.tileset;
  }

  public ngOnInit(): void {
    if (!this.map) {
      console.error("Attempt to export before map is ready");
      return;
    }
    this.updateExportOptions();
    this.map.on("moveend", this.updateExportOptionsAfterBind);
    this.map.on("resize", this.updateExportOptionsAfterBind);
  }

  public ngOnDestroy(): void {
    this.map.off("moveend", this.updateExportOptionsAfterBind);
    this.map.off("resize", this.updateExportOptionsAfterBind);
  }

  public close(): void {
    this.dialogRef.close();
  }

  public getExportLink(zoom: number): string {
    const mapState = this.getMapState();
    return `${environment.tile_domain}/export/pdf/${zoom}/${mapState.minX}/${mapState.minY}/${mapState.maxX}/${mapState.maxY}/${this.tileset.name}`
  }

  public exportInitiated(): void {
    this.exportInProgress = true;
    this.snackBar.open(`Exporting... Please wait`, undefined, {
      duration: 2000
    });
    window.setTimeout(() => {
      this.close();
    }, 500)
  }

  public getExportName(zoom: number): string {
    return `${this.tileset.name}-${zoom}.pdf`
  }

  private updateExportOptions(): void {
      this.exportInfos = this.exportInfos.map(() => {
        return {is_placeholder: true};
      });
      const mapState = this.getMapState();
      const minZoom = Math.max(mapState.zoom, this.tileset.zoom_min);
      const infoRequestObservables = [];
      for(let i = minZoom; i <= this.tileset.zoom_max; i++) {
        infoRequestObservables.push(this.http.get(`${environment.tile_domain}/export/info/${i}/${mapState.minX}/${mapState.minY}/${mapState.maxX}/${mapState.maxY}/${this.tileset.name}`));
      }
      forkJoin(infoRequestObservables).subscribe((results: HttpResponse<ExportInfo>[]) => {
        this.exportInfos = (<any>results).filter((exportInfo: ExportInfo) => exportInfo.permitted).map(exportInfo => Object.assign({}, exportInfo, {is_placeholder: false}));
      });
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
    const [minX, minY, maxX, maxY] = this.map.getBounds().toBBoxString().split(",")
    return {
      minX: minX,
      minY: minY,
      maxX: maxX,
      maxY: maxY,
      zoom: this.map.getZoom()
    };
  }
}
