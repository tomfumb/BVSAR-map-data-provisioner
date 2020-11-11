import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from  '@angular/material/dialog';

@Component({
  selector: 'app-tile-urls',
  templateUrl: './tile-urls.component.html',
  styleUrls: ['./tile-urls.component.less']
})
export class TileUrlsComponent {
  
  constructor(
    private dialogRef: MatDialogRef<TileUrlsComponent>,
    @Inject(MAT_DIALOG_DATA)
    public data: any
  ) {

  }

  public closeMe() {
      this.dialogRef.close();
  }
}