import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import * as l from 'leaflet';

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
  private readonly MAX_PRECISION_DD = 5;
  private readonly MAX_PRECISION_DDM = 4;

  constructor(
    private dialogRef: MatDialogRef<ReCentreComponent>,
    @Inject(MAT_DIALOG_DATA) public data: Parameters
  ) {
    this.map = data.map;
    const centre = this.map.getCenter()
    this.latitudeDd = this.roundTo(centre.lat, this.MAX_PRECISION_DD);
    this.longitudeDd = this.roundTo(centre.lng, this.MAX_PRECISION_DD);
  }

  public ngOnInit(): void {
    this.conversions.fromDecimal();
  }

  public update(): void {
    this.map.setView(l.latLng(this.latitudeDd, this.longitudeDd), this.map.getZoom());
    this.dialogRef.close();
  }

  private roundTo(input: number, precision: number): number {
    const scaleFactor = Math.pow(10, precision);
    return Math.round(input * scaleFactor) / scaleFactor;
  }

  public readonly conversions = {
    fromDecimal: () => {
      const latitudeParts = this.latitudeDd.toString().split(".").map(part => parseInt(part, 10));
      const longitudeParts = this.longitudeDd.toString().split(".").map(part => parseInt(part, 10));
      this.latitudeDmsD = latitudeParts[0];
      this.longitudeDmsD = longitudeParts[0];
      this.latitudeDdmD = this.latitudeDmsD;
      this.longitudeDdmD = this.longitudeDmsD;
      const latitudeMParts = (latitudeParts.length == 2 ? (this.latitudeDd - latitudeParts[0]) * 60 : 0).toString().split(".").map(part => Math.abs(parseInt(part, 10)));
      const longitudeMParts = (longitudeParts.length == 2 ? (this.longitudeDd - longitudeParts[0]) * 60 : 0).toString().split(".").map(part => Math.abs(parseInt(part, 10)));
      this.latitudeDmsM = latitudeMParts[0];
      this.longitudeDmsM = longitudeMParts[0];
      this.latitudeDdmM = this.roundTo(parseFloat(latitudeMParts.join(".")), this.MAX_PRECISION_DDM);
      this.longitudeDdmM = this.roundTo(parseFloat(longitudeMParts.join(".")), this.MAX_PRECISION_DDM);
      this.latitudeDmsS = Math.round(parseFloat(["0",latitudeMParts[1]].join(".")) * 60);
      this.longitudeDmsS = Math.round(parseFloat(["0",longitudeMParts[1]].join(".")) * 60);
    }
  };
}
