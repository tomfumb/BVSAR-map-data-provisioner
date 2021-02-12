import { HttpClient, HttpErrorResponse, HttpEventType } from '@angular/common/http';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from 'src/environments/environment';
import { SpaceService } from '../space.service';

interface Upload {
  filename: string;
  path: string;
  bytes: number;
  uploaded: number;
}

interface UploadControlStatus {
  pickerEnabled: boolean;
  executeEnabled: boolean;
  message: string;
}

@Component({
  selector: 'app-share',
  templateUrl: './share.component.html',
  styleUrls: ['./share.component.less']
})
export class ShareComponent {

  public uploads: Upload[] = [];
  public uploadDomain: string = environment.tile_domain;
  
  private readonly FILE_BYTE_LIMIT = 100000000;

  private pendingUpload: File;
  private uploadPermitted: boolean = true;
  private uploadInProgress: boolean = false;
  private uploadProgress = 0;
  private uploadError: string = "";

  @ViewChild("fileSelector")
  private fileSelector: ElementRef;

  constructor(
    private http: HttpClient,
    private spaceService: SpaceService
  ) {
    this.updateFileList();
  }

  public fileChange(event): void {
    this.uploadError = "";
    this.uploadPermitted = true;
    this.pendingUpload = event.target.files.length > 0 ? event.target.files[0] : null;
    if (this.pendingUpload) {
      // not validated in API because limited user-base, likely not malicious users, and overlay fs means any damaga is undone by reboot
      if (this.pendingUpload.size > this.FILE_BYTE_LIMIT) {
        this.uploadError = `File is too big. File: ${this.spaceService.fromBytes(this.pendingUpload.size)}, limit: ${this.spaceService.fromBytes(this.FILE_BYTE_LIMIT)}`;
        this.uploadPermitted = false;
      }
    }
  }

  public uploadFile(): void {
    const formData = new FormData();
    formData.append("file", this.pendingUpload);
    this.uploadInProgress = true;
    this.http.post(`${environment.tile_domain}/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    }).pipe(catchError((error: HttpErrorResponse) => {
      this.uploadInProgress = false;
      this.uploadProgress = 0;
      window.alert(error.message);
      return throwError(error);
    })).subscribe(response => {
      switch (response.type) {
        case HttpEventType.Response:
          this.uploadProgress = 0;
          this.uploadInProgress = false;
          this.pendingUpload = null;
          this.fileSelector.nativeElement.value = null;
          this.updateFileList();
          break;
        case HttpEventType.UploadProgress:
          if (response.total > 0) {
            this.uploadProgress = response.loaded / response.total * 100;
          }
          break;
      }
    });
  }

  public get uploadControlStatus(): UploadControlStatus {
    let message: string = "";
    if (this.uploadPermitted) {
      if (this.uploadInProgress) {
        message = "Uploading..."
      } else {
        if (this.pendingUpload) {
          message = `Ready to upload (${this.spaceService.fromBytes(this.pendingUpload ? this.pendingUpload.size : 0)})`;
        }
      }
    } else {
      if (this.uploadError) {
        message = this.uploadError;
      }
    }
    return {
      pickerEnabled: !this.uploadInProgress,
      executeEnabled: this.uploadPermitted && !!this.pendingUpload && !this.uploadInProgress,
      message: message
    };
  }

  public get uploadProgressPct(): string {
    return `${this.uploadProgress}%`;
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
