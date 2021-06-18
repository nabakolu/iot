import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HeatingControlComponent } from './heating-control.component';

describe('HeatingControlComponent', () => {
  let component: HeatingControlComponent;
  let fixture: ComponentFixture<HeatingControlComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ HeatingControlComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HeatingControlComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
