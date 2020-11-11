import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from  '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { CopyService } from 'src/app/copy.service';

interface Parameters {
  tilesetName: string;
}

@Component({
  selector: 'app-tile-urls',
  templateUrl: './tile-urls.component.html',
  styleUrls: ['./tile-urls.component.less']
})
export class TileUrlsComponent {

  public static readonly WIDTH = "80%";
  public static readonly PANEL_CLASS = "common-modal-panel";

  public tileUrls: {[index: string]: string} = {};
  
  constructor(
    private dialogRef: MatDialogRef<TileUrlsComponent>,
    private snackBar: MatSnackBar,
    private copyService: CopyService,
    @Inject(MAT_DIALOG_DATA) public data: Parameters
  ) {
    this.tileUrls = this.buildTileUrls(data);
  }

  public close() {
      this.dialogRef.close();
  }

  public keepOriginalOrder(a: any, _: any): string {
    return a.key;
  }

  public copyUrl(url: string): void {
    this.copyService.copyText(url);
    this.snackBar.open(`Copied URL`, undefined, {
      duration: 2000
    });
    window.setTimeout(() => {
      this.close()
    }, 500);
  }

  private buildTileUrls(parameters: Parameters): {[index: string]: string} {
    const baseUrl = `${window.location.protocol}//${window.location.host}/tiles/files/${parameters.tilesetName}/`
    return {
      "GIS Kit": `${baseUrl}#Z#/#X#/#Y#.png`,
      "Touch GIS": `${baseUrl}{z}/{x}/{y}.png`,
      "QGIS": `${baseUrl}{z}/{x}/{y}.png`
    };
  }
}
