import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { environment } from 'src/environments/environment';
import { SpaceService } from '../space.service';

interface DirListing {
  dirs: {
    [index: string]: DirListing;
  };
  files: {
    name: string;
    path: string;
    size: number;
  }[];
}

@Component({
  selector: 'app-files',
  templateUrl: './files.component.html',
  styleUrls: ['./files.component.less']
})
export class FilesComponent implements OnInit {

  public listing: DirListing = {dirs: {}, files: []};

  constructor(
    private http: HttpClient,
    private spaceService: SpaceService
  ) { }

  public ngOnInit(): void {
    this.http.get<DirListing>(`${environment.tile_domain}/files/list`).subscribe(response => {
      this.listing = response;
    });
  }

  public formatSize(bytes: number): string {
    return this.spaceService.fromBytes(bytes);
  }
}