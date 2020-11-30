import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import * as l from 'leaflet';
import { CoordinateService } from 'src/app/coordinate.service';

interface Parameters {
  map: l.map;
}

@Component({
  selector: 'app-re-centre',
  templateUrl: './re-centre.component.html',
  styleUrls: ['./re-centre.component.less']
})
export class ReCentreComponent implements OnInit {

  public static readonly WIDTH = "80%";
  public static readonly PANEL_CLASS = "common-modal-panel";

  public latitudeDd: number;
  public longitudeDd: number;

  public latitudeDdmD: number;
  public latitudeDdmM: number;
  public longitudeDdmD: number;
  public longitudeDdmM: number;

  public latitudeDmsD: number;
  public latitudeDmsM: number;
  public latitudeDmsS: number;
  public longitudeDmsD: number;
  public longitudeDmsM: number;
  public longitudeDmsS: number;

  private map: l.map;

  constructor(
    private dialogRef: MatDialogRef<ReCentreComponent>,
    private coordinateService: CoordinateService,
    @Inject(MAT_DIALOG_DATA) public data: Parameters
  ) {
    this.map = data.map;
  }

  public ngOnInit(): void {
    const centre = this.map.getCenter()
    this.latitudeDd = this.coordinateService.roundTo(centre.lat, CoordinateService.MAX_PRECISION_DD);
    this.longitudeDd = this.coordinateService.roundTo(centre.lng, CoordinateService.MAX_PRECISION_DD);
    this.ddChanged();
  }

  public update(): void {
    this.map.setView(l.latLng(this.latitudeDd, this.longitudeDd), this.map.getZoom());
    this.dialogRef.close();
  }

  public ddChanged(): void {
    this.updateDdmFromDd();
    this.updateDmsFromDd();
  }

  public ddmChanged(): void {
    this.latitudeDd = this.coordinateService.roundTo(this.coordinateService.ddmToDd({
      d: this.latitudeDdmD,
      m: this.latitudeDdmM
    }), CoordinateService.MAX_PRECISION_DD);
    this.longitudeDd = this.coordinateService.roundTo(this.coordinateService.ddmToDd({
      d: this.longitudeDdmD,
      m: this.longitudeDdmM
    }), CoordinateService.MAX_PRECISION_DD);
    this.updateDmsFromDd();
  }

  public dmsChanged(): void {
    this.latitudeDd = this.coordinateService.roundTo(this.coordinateService.dmsToDd({
      d: this.latitudeDmsD,
      m: this.latitudeDmsM,
      s: this.latitudeDmsS
    }), CoordinateService.MAX_PRECISION_DD);
    this.longitudeDd = this.coordinateService.roundTo(this.coordinateService.dmsToDd({
      d: this.longitudeDmsD,
      m: this.longitudeDmsM,
      s: this.longitudeDmsS
    }), CoordinateService.MAX_PRECISION_DD);
    this.updateDdmFromDd();
  }

  private updateDmsFromDd(): void {
    const latitudeDms = this.coordinateService.ddToDms(this.latitudeDd);
    const longitudeDms = this.coordinateService.ddToDms(this.longitudeDd);
    this.latitudeDmsD = latitudeDms.d;
    this.latitudeDmsM = latitudeDms.m;
    this.latitudeDmsS = latitudeDms.s;
    this.longitudeDmsD = longitudeDms.d;
    this.longitudeDmsM = longitudeDms.m;
    this.longitudeDmsS = longitudeDms.s;
  }

  private updateDdmFromDd(): void {
    const latitudeDdm = this.coordinateService.ddToDdm(this.latitudeDd);
    const longitudeDdm = this.coordinateService.ddToDdm(this.longitudeDd);
    this.latitudeDdmD = latitudeDdm.d;
    this.latitudeDdmM = this.coordinateService.roundTo(latitudeDdm.m, CoordinateService.MAX_PRECISION_DDM);
    this.longitudeDdmD = longitudeDdm.d;
    this.longitudeDdmM = this.coordinateService.roundTo(longitudeDdm.m, CoordinateService.MAX_PRECISION_DDM);
  }
}
