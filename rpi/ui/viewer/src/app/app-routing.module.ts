import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { FilesComponent } from './files/files.component';
import { MapComponent } from './map/map.component';
import { ShareComponent } from './share/share.component';

const routes: Routes = [
  { path: "share", component: ShareComponent },
  { path: "map", component: MapComponent },
  { path: "files", component: FilesComponent },
  { path: "", redirectTo: "map", pathMatch: "full"}
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { useHash: true })],
  exports: [RouterModule]
})
export class AppRoutingModule { }
