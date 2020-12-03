import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { environment } from 'src/environments/environment';
import { SpaceService } from '../space.service';

interface DirFiles {[index: string]: {
  path: string,
  size: number
}};

@Component({
  selector: 'app-files',
  templateUrl: './files.component.html',
  styleUrls: ['./files.component.less']
})
export class FilesComponent implements OnInit {

  public dirFiles: DirFiles = {};

  constructor(
    private http: HttpClient,
    private spaceService: SpaceService
  ) { }

  public ngOnInit(): void {
    this.http.get<DirFiles>(`${environment.tile_domain}/files/list`).subscribe(response => {
      this.dirFiles = response;
    });
  }

  public stripParentDirs(path: string): string {
    const pathParts = path.split("/");
    return pathParts.length > 1 ? pathParts.slice(-1)[0] : path;
  }

  public formatSize(bytes: number): string {
    return this.spaceService.fromBytes(bytes);
  }
}