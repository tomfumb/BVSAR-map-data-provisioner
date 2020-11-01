import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { environment } from 'src/environments/environment';
import { SpaceService } from '../space.service';

interface Status {
  space: {
    available: number;
  };
  power: {
    remaining: number;
  };
}

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.less']
})
export class HeaderComponent implements OnInit {

  public powerText: string;
  public powerClass: string;

  public spaceText: string;
  public spaceClass: string;

  private readonly POLL_INTERVAL: number = 15;

  constructor(
    private http: HttpClient,
    private spaceService: SpaceService
  ) { }

  public ngOnInit(): void {
    this.poll();
  }

  private poll(): void {
    this.http.get<Status>(`${environment.tile_domain}/status`).subscribe(status => {
      this.powerText = `Power: ${status.power.remaining}%`;
      this.powerClass = this.getPowerClass(status.power.remaining);
      this.spaceText = `Space: ${this.spaceService.fromBytes(status.space.available)}`;
      this.spaceClass = this.getSpaceClass(status.space.available);
      window.setTimeout(this.poll.bind(this), this.POLL_INTERVAL * 1000);
    })
  }

  private getPowerClass(power: number): string {
    if (power >= 50) {
      return "power-good";
    }
    if (power >= 15) {
      return "power-low";
    }
    return "power-critical";
  }

  private getSpaceClass(bytes: number): string {
    if (bytes >= 1000000000) {
      return "space-good";
    }
    return "space-critical";
  }
}
