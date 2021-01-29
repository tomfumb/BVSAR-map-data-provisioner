import { HttpClient, HttpEventType } from '@angular/common/http';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { environment } from 'src/environments/environment';
import { SpaceService } from '../space.service';

interface Upload {
  filename: string;
  path: string;
  bytes: number;
  uploaded: number;
}

@Component({
  selector: 'app-share',
  templateUrl: './share.component.html',
  styleUrls: ['./share.component.less']
})
export class ShareComponent {

  public uploads: Upload[] = [];
  public uploadDomain: string = environment.tile_domain;
  
  private pendingUpload: File;
  private readonly FILE_BYTE_LIMIT = 100000000;

  @ViewChild("fileSelector")
  private fileSelector: ElementRef;

  constructor(
    private http: HttpClient,
    private spaceService: SpaceService
  ) {
    this.updateFileList();
  }

  public fileChange(event): void {
    const candidateFile = event.target.files.length > 0 ? event.target.files[0] : null;
    if (candidateFile) {
      // not validated in API because limited user-base, likely not malicious users, and overlay fs means any damaga is undone by reboot
      if (candidateFile.size > this.FILE_BYTE_LIMIT) {
        window.alert(`File is too big and cannot be uploaded. File: ${this.spaceService.fromBytes(candidateFile.size)}, limit: ${this.spaceService.fromBytes(this.FILE_BYTE_LIMIT)}`);
        this.pendingUpload = null;
      } else {
        this.pendingUpload = candidateFile;
      }
    } else {
      this.pendingUpload = null;
    }
  }

  public uploadFile(): void {
    const formData = new FormData();
    formData.append("file", this.pendingUpload);
    this.http.post(`${environment.tile_domain}/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    }).subscribe(response => {
      if (response.type === HttpEventType.Response) {
        this.pendingUpload = null;
        this.fileSelector.nativeElement.value = null;
        this.updateFileList();
      }
    });
  }

  public get pendingUploadExists(): boolean {
    return !!this.pendingUpload;
  }

  public get pendingUploadButtonText(): string {
    return "Upload" + (this.pendingUpload ? ` (${this.spaceService.fromBytes(this.pendingUpload.size)})` : "")
  }

  public formatSize(bytes: number): string {
    return this.spaceService.fromBytes(bytes);
  }

  private updateFileList(): void {
    this.http.get<Upload[]>(`${environment.tile_domain}/upload/list`).subscribe(response => {
      this.uploads = response.sort((a, b) => {
        return b.uploaded - a.uploaded;
      });
    });
  }
}
