import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import * as l from 'leaflet';

interface Parameters {
  map: l.map;
}

type DD = number;

interface DDM {
  d: number;
  m: number;
}

interface DMS {
  d: number;
  m: number;
  s: number;
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
  }

  public ngOnInit(): void {
    const centre = this.map.getCenter()
    this.latitudeDd = this.roundTo(centre.lat, this.MAX_PRECISION_DD);
    this.longitudeDd = this.roundTo(centre.lng, this.MAX_PRECISION_DD);
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
    this.latitudeDd = this.roundTo(this.conversions.ddmToDd({
      d: this.latitudeDdmD,
      m: this.latitudeDdmM
    }), this.MAX_PRECISION_DD);
    this.longitudeDd = this.roundTo(this.conversions.ddmToDd({
      d: this.longitudeDdmD,
      m: this.longitudeDdmM
    }), this.MAX_PRECISION_DD);
    this.updateDmsFromDd();
  }

  public dmsChanged(): void {
    this.latitudeDd = this.roundTo(this.conversions.dmsToDd({
      d: this.latitudeDmsD,
      m: this.latitudeDmsM,
      s: this.latitudeDmsS
    }), this.MAX_PRECISION_DD);
    this.longitudeDd = this.roundTo(this.conversions.dmsToDd({
      d: this.longitudeDmsD,
      m: this.longitudeDmsM,
      s: this.longitudeDmsS
    }), this.MAX_PRECISION_DD);
    this.updateDdmFromDd();
  }

  private updateDmsFromDd(): void {
    const latitudeDms = this.conversions.ddToDms(this.latitudeDd);
    const longitudeDms = this.conversions.ddToDms(this.longitudeDd);
    this.latitudeDmsD = latitudeDms.d;
    this.latitudeDmsM = latitudeDms.m;
    this.latitudeDmsS = latitudeDms.s;
    this.longitudeDmsD = longitudeDms.d;
    this.longitudeDmsM = longitudeDms.m;
    this.longitudeDmsS = longitudeDms.s;
  }

  private updateDdmFromDd(): void {
    const latitudeDdm = this.conversions.ddToDdm(this.latitudeDd);
    const longitudeDdm = this.conversions.ddToDdm(this.longitudeDd);
    this.latitudeDdmD = latitudeDdm.d;
    this.latitudeDdmM = this.roundTo(latitudeDdm.m, this.MAX_PRECISION_DDM);
    this.longitudeDdmD = longitudeDdm.d;
    this.longitudeDdmM = this.roundTo(longitudeDdm.m, this.MAX_PRECISION_DDM);
  }

  private roundTo(input: number, precision: number): number {
    const scaleFactor = Math.pow(10, precision);
    return Math.round(input * scaleFactor) / scaleFactor;
  }

  public readonly conversions = {
    ddToDms: (dd: DD): DMS => {
      const M = this.conversions.ddToM(dd);
      return {
          d : 0|dd,
          m : 0|M/1e7,
          s : (0|Math.abs(dd)*60%1*6000)/100
      };
    },
    ddToDdm: (dd: DD): DDM => {
      return {
          d : 0|dd,
          m : this.conversions.ddToM(dd)/1e7
      };
    },
    dmsToDd: (dms: DMS): DD => {
      return dms.d + dms.m/60 + dms.s/(60*60);
    },
    ddmToDd: (ddm: DDM): DD => {
      return ddm.d + ddm.m / 60;
    },
    ddToM: (dd: DD): number => {
      return 0|((dd<0?-dd:dd)%1)*60e7;
    }
  };
}
