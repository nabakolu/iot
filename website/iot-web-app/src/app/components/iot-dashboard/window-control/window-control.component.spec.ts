import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WindowControlComponent } from './window-control.component';

describe('WindowControlComponent', () => {
  let component: WindowControlComponent;
  let fixture: ComponentFixture<WindowControlComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ WindowControlComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(WindowControlComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
