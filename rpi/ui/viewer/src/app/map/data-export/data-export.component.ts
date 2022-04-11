import { Component, OnInit, Inject } from '@angular/core';
import * as l from 'leaflet';
import { MatDialogRef, MAT_DIALOG_DATA } from  '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { interval, Observable, Observer } from 'rxjs';
import { environment } from 'src/environments/environment';
import { catchError, map } from 'rxjs/operators';

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
  public dataTypeCountPending: boolean = false;
  public readonly dataTypeCountLoadingText = interval(300)
    .pipe(
      map(i => new Array((i % 3) + 1).fill(".").join("")
    )
  );

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
    this.dataTypeCountPending = true;
    delete this.dataTypeCounts[dataType];
    const [minX, minY, maxX, maxY] = this.getBoundingBox();
    this.http.get(`${environment.tile_domain}/data/${dataType}/count/${minX}/${minY}/${maxX}/${maxY}`).pipe(catchError((error: any, caught: Observable<Object>) => {
      this.dataTypeCountPending = false;
      return caught;
    })).subscribe((response: HttpResponse<number>) => {
      this.dataTypeCounts[dataType] = <any>response;
      this.dataTypeCountPending = false;
    })
  }

  public getExportLink(dataType: string): string {
    const [minX, minY, maxX, maxY] = this.getBoundingBox();
    return `${environment.tile_domain}/data/${dataType}/export/${minX}/${minY}/${maxX}/${maxY}`
  }

  public exportInitiated(): void {
    this.snackBar.open(`Exporting... Please wait`, undefined, {
      duration: 2000
    });
    window.setTimeout(() => {
      this.close();
    }, 500)
  }

  public close(): void {
    this.dialogRef.close();
  }

  private getBoundingBox(): number[] {
    return this.map.getBounds().toBBoxString().split(",");
  }
}
