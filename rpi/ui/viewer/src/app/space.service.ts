import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class SpaceService {

  constructor() { }

  // adapted from https://stackoverflow.com/a/20732091/519575
  public fromBytes(bytes): string {
      const i = bytes == 0 ? 0 : Math.floor( Math.log(bytes) / Math.log(1024) );
      return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
  }
}
