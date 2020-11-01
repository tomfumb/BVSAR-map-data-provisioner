import { HttpClient, HttpEventType, HttpParams, HttpRequest, HttpResponse } from '@angular/common/http';
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
  private pendingDeleteFilename: string;

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
      if (candidateFile.size > 100000000) {
        window.alert("File is too big and cannot be uploaded");
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
    const options = {
      params: new HttpParams(),
      reportProgress: true,
    };
    const req = new HttpRequest("POST", `${environment.tile_domain}/upload`, formData, options);
    this.http.request(req).subscribe(() => {
      this.pendingUpload = null;
      this.fileSelector.nativeElement.value = null;
      this.updateFileList();
    });
  }

  public get pendingUploadExists(): boolean {
    return !!this.pendingUpload;
  }

  public get pendingUploadButtonText(): string {
    return "Upload" + (this.pendingUpload ? ` ${this.pendingUpload.name} (${this.spaceService.fromBytes(this.pendingUpload.size)})` : "")
  }

  public deleteFileInitiate(filename: string): void {
    this.pendingDeleteFilename = filename;
  }

  public deleteFileCancel(): void {
    this.pendingDeleteFilename = null;
  }

  public deleteFile(): void {
    this.http.delete(`${environment.tile_domain}/upload/${this.pendingDeleteFilename}`).subscribe(() => {
      this.updateFileList();
    });
  }

  private updateFileList(): void {
    this.http.get<Upload[]>(`${environment.tile_domain}/upload/list`).subscribe(response => {
      this.uploads = response.sort((a, b) => {
        return b.uploaded - a.uploaded;
      });
    });
  }
}
