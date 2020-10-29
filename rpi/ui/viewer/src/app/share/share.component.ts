import { HttpClient, HttpEventType, HttpParams, HttpRequest, HttpResponse } from '@angular/common/http';
import { Component } from '@angular/core';
import { environment } from 'src/environments/environment';

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

  constructor(
    private http: HttpClient
  ) {
    this.updateFileList();
  }

  public fileChange(event): void {
    this.pendingUpload = event.target.files.length > 0 ? event.target.files[0] : null;
  }

  public uploadFile(): void {
    const formData = new FormData();
    formData.append("file", this.pendingUpload);
    const options = {
      params: new HttpParams(),
      reportProgress: true,
    };
    const req = new HttpRequest("POST", `${environment.tile_domain}/upload`, formData, options);
    this.http.request(req).subscribe(
      event => {
        if (event.type == HttpEventType.UploadProgress) {
          const percentDone = Math.round(100 * event.loaded / event.total);
          console.log(`File is ${percentDone}% loaded.`);
        } else if (event instanceof HttpResponse) {
          console.log('File is completely loaded!');
        }
      },
      (err) => {
        console.log("Upload Error:", err);
      }, () => {
        console.log("Upload done");
        this.pendingUpload = null;
        this.updateFileList();
      }
    );
  }

  public get pendingUploadExists(): boolean {
    return !!this.pendingUpload;
  }

  public get pendingUploadButtonText(): string {
    return "Upload" + (this.pendingUpload ? ` ${this.pendingUpload.name} (${this.pendingUpload.size} bytes)` : "")
  }

  public deleteFileInitiate(filename: string): void {
    this.pendingDeleteFilename = filename;
  }

  public deleteFileCancel(): void {
    this.pendingDeleteFilename = null;
  }

  public deleteFile(): void {
    this.http.delete(`${environment.tile_domain}/uploads/${this.pendingDeleteFilename}`).subscribe(() => {
      this.updateFileList();
    });
  }

  private updateFileList(): void {
    this.http.get<Upload[]>(`${environment.tile_domain}/uploads/list`).subscribe(response => {
      this.uploads = response;
    });
  }
}
