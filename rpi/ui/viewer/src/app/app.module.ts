import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { MapComponent } from './map/map.component';
import { HttpClientModule } from '@angular/common/http';
import { ShareComponent } from './share/share.component';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSnackBarModule } from '@angular/material/snack-bar'
import { TileUrlsComponent } from './map/tile-urls/tile-urls.component';
import { PdfExportComponent } from './map/pdf-export/pdf-export.component';
import { FilesComponent } from './files/files.component';
import { ReCentreComponent } from './map/re-centre/re-centre.component';
import { DatetimePipe } from './datetime.pipe';
import { BenchComponent } from './map/mode-providers/bench/bench.component';
import { AttributionComponent } from './map/attribution/attribution.component';
import { DataExportComponent } from './map/data-export/data-export.component';

@NgModule({
  declarations: [
    AppComponent,
    MapComponent,
    ShareComponent,
    TileUrlsComponent,
    PdfExportComponent,
    FilesComponent,
    ReCentreComponent,
    DatetimePipe,
    BenchComponent,
    AttributionComponent,
    DataExportComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    CommonModule,
    NoopAnimationsModule,
    MatDialogModule,
    MatSnackBarModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
