import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Tileset } from '../tileset';


interface Parameters {
  tileset: Tileset;
}

@Component({
  selector: 'app-attribution',
  templateUrl: './attribution.component.html',
  styleUrls: ['./attribution.component.less']
})
export class AttributionComponent {

  public static readonly WIDTH = "80%";
  public static readonly PANEL_CLASS = "common-modal-panel";

  public tilesetName: string = "";
  public attributionEntries: string[] = [];

  constructor(
    private dialogRef: MatDialogRef<AttributionComponent>,
    @Inject(MAT_DIALOG_DATA) private data: Parameters
  ) {
    this.tilesetName = data.tileset.name;
    this.attributionEntries = data.tileset.attribution;
  }
}
