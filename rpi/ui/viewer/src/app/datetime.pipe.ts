import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'datetime'
})
export class DatetimePipe implements PipeTransform {

  transform(value: number): string {
    const date = new Date(value)
    return `${date.getFullYear()}/${this.padZeros(date.getMonth() + 1)}/${this.padZeros(date.getDate())} ${this.padZeros(date.getHours())}:${this.padZeros(date.getMinutes())}:${this.padZeros(date.getSeconds())}`
  }

  padZeros(int: number): string {
    return int < 10 ? `0${int}` : int.toString();
  }
}
