import { Injectable } from '@angular/core';

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

@Injectable({
  providedIn: 'root'
})
export class CoordinateService {

  public static readonly MAX_PRECISION_DD = 5;
  public static readonly MAX_PRECISION_DDM = 4;

  constructor() { }

  public roundTo(input: number, precision: number): number {
    const scaleFactor = Math.pow(10, precision);
    return Math.round(input * scaleFactor) / scaleFactor;
  }

  public ddToDms(dd: DD): DMS {
    const M = this.ddToM(dd);
    return {
        d : 0|dd,
        m : 0|M/1e7,
        s : (0|Math.abs(dd)*60%1*6000)/100
    };
  }

  public ddToDdm(dd: DD): DDM {
    return {
        d : 0|dd,
        m : this.ddToM(dd)/1e7
    };
  }

  public dmsToDd(dms: DMS): DD {
    const decimalPart = dms.m / 60 + dms.s / 3600;
    return dms.d > 0 ? dms.d + decimalPart : dms.d - decimalPart;
  }

  public ddmToDd(ddm: DDM): DD {
    const decimalPart = ddm.m / 60;
    return ddm.d > 0 ? ddm.d + decimalPart : ddm.d - decimalPart;
  }

  public ddToM(dd: DD): number {
    return 0|((dd<0?-dd:dd)%1)*60e7;
  }
}
