import { Component, OnInit, Inject } from '@angular/core';
import * as l from 'leaflet';
import { MatDialogRef, MAT_DIALOG_DATA } from  '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { Observable, Observer } from 'rxjs';
import { environment } from 'src/environments/environment';

interface Parameters {
  map: l.map;
}

@Component({
  selector: 'app-data-export',
  templateUrl: './data-export.component.html',
  styleUrls: ['./data-export.component.less']
})
export class DataExportComponent implements OnInit {

  public contentVisible: boolean = false;
  public dataTypes: string[] = [];
  public dataTypeCounts: {[index: string]: number} = {};

  private map: l.map;
  private initObserver?: Observer<void> = undefined;

  constructor(
    private dialogRef: MatDialogRef<DataExportComponent>,
    private snackBar: MatSnackBar,
    private http: HttpClient,
    @Inject(MAT_DIALOG_DATA) public data: Parameters
  ) {
    this.map = data.map;
    new Observable((observer) => {
      this.initObserver = observer;
    }).subscribe(() => {
      this.contentVisible = true;
    })
  }

  public ngOnInit(): void {
    if (!this.map) {
      console.error("Attempt to export before map is ready");
      return;
    }
    this.http.get(`${environment.tile_domain}/data/list`).subscribe((response: HttpResponse<string>[]) => {
      this.dataTypes = <any>response;
      this.initObserver.next();
      this.initObserver.complete();
    })
  }

  public populateCount(dataType: string): void {
    const [minX, minY, maxX, maxY] = this.getBoundingBox();
    this.http.get(`${environment.tile_domain}/data/${dataType}/count/${minX}/${minY}/${maxX}/${maxY}`).subscribe((response: HttpResponse<number>) => {
      this.dataTypeCounts[dataType] = <any>response;
    })
  }

  private getBoundingBox(): number[] {
    return this.map.getBounds().toBBoxString().split(",");
  }
}
