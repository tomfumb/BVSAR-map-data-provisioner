import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class TouchService {

  constructor() { }

  public get touchEnabled(): boolean { 
    return "ontouchstart" in window || navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0; 
  } 
}
