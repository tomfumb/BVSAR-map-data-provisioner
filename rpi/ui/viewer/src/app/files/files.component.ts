import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { environment } from 'src/environments/environment';
import { SpaceService } from '../space.service';

interface File {
  name: string;
  path: string;
  size: number;
  uploaded: number;
}

interface DirListing {
  id: string;
  dirs: {
    [index: string]: DirListing;
  };
  files: File[];
}

@Component({
  selector: 'app-files',
  templateUrl: './files.component.html',
  styleUrls: ['./files.component.less']
})
export class FilesComponent implements OnInit {

  public listing: DirListing = {id: "", dirs: {}, files: []};
  private expanded: string[] = []

  constructor(
    private http: HttpClient,
    private spaceService: SpaceService
  ) { }

  public ngOnInit(): void {
    this.http.get<DirListing>(`${environment.tile_domain}/files/list`).subscribe(response => {
      this.listing = response;
      this.expanded = Object.values(this.listing.dirs).map(entry => entry.id);
    });
  }

  public formatSize(bytes: number): string {
    return this.spaceService.fromBytes(bytes);
  }

  public isExpanded(id: string): boolean {
    return this.expanded.indexOf(id) > -1;
  }

  public collapse(id: string): void {
    if (this.isExpanded(id)) {
      this.expanded = this.expanded.filter(entry => entry !== id);
    }
  }

  public expand(id: string): void {
    if (!this.isExpanded(id)) {
      this.expanded = this.expanded.concat([id]);
    }
  }

  public fileSort(files: File[]): File[] {
    const filesCopy = files.slice(0);
    filesCopy.sort((a: File, b: File) => {
      return b.uploaded - a.uploaded;
    });
    return filesCopy;
  }
}