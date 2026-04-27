import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface FilterState {
  startDate: string;
  endDate: string;
  region: string;
  violenceTypes: string[];
}

@Component({
  selector: 'app-stats-filters',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './stats-filters.component.html',
  styleUrls: ['./stats-filters.component.css'],
})
export class StatsFiltersComponent implements OnInit {
  @Input() filters: FilterState = {
    startDate: '2000-01-01',
    endDate: '2024-12-31',
    region: 'all',
    violenceTypes: ['all'],
  };

  @Output() filtersChanged = new EventEmitter<FilterState>();
  @Output() filtersReset = new EventEmitter<void>();

  // FILTROS POR DEFECTO
  // Datos quemados - Regiones disponibles
  regions = [
    { value: 'all', label: 'Todas las Regiones' },
    { value: 'africa', label: 'África' },
    { value: 'americas', label: 'América' },
    { value: 'asia', label: 'Asia' },
    { value: 'europe', label: 'Europa' },
    { value: 'middle-east', label: 'Medio Oriente' },
    { value: 'oceania', label: 'Oceanía' },
  ];

  // Datos quemados - Tipos de violencia
  violenceTypeOptions = [
    { value: 'all', label: 'Todos los Tipos', checked: true },
    { value: 'state-based', label: 'State-based Conflict', checked: false },
    { value: 'non-state', label: 'Non-state Conflict', checked: false },
    { value: 'one-sided', label: 'One-sided Violence', checked: false },
  ];

  // Presets rápidos de fechas
  datePresets = [
    { label: 'Todo el periodo', start: '1989-01-01', end: '2024-12-31' },
    { label: 'Últimos 10 años', start: '2014-01-01', end: '2024-12-31' },
    { label: 'Últimos 5 años', start: '2019-01-01', end: '2024-12-31' },
    { label: 'Década 2010s', start: '2010-01-01', end: '2019-12-31' },
    { label: 'Década 2000s', start: '2000-01-01', end: '2009-12-31' },
  ];

  // Estado local de filtros
  localFilters: FilterState = { ...this.filters };

  ngOnInit() {
    this.localFilters = { ...this.filters };
    this.updateViolenceTypeChecks();
  }

  // Actualizar checkboxes según el estado inicial
  private updateViolenceTypeChecks() {
    if (this.localFilters.violenceTypes.includes('all')) {
      this.violenceTypeOptions[0].checked = true;
      this.violenceTypeOptions.slice(1).forEach((opt) => (opt.checked = false));
    } else {
      this.violenceTypeOptions[0].checked = false;
      this.violenceTypeOptions.slice(1).forEach((opt) => {
        opt.checked = this.localFilters.violenceTypes.includes(opt.value);
      });
    }
  }

  // Aplicar preset de fecha
  applyDatePreset(preset: any) {
    this.localFilters.startDate = preset.start;
    this.localFilters.endDate = preset.end;
  }

  // Cambiar tipo de violencia (checkbox)
  onViolenceTypeChange(option: any) {
    if (option.value === 'all') {
      this.violenceTypeOptions.forEach((opt) => {
        opt.checked = opt.value === 'all';
      });
      this.localFilters.violenceTypes = ['all'];
    } else {
      this.violenceTypeOptions[0].checked = false;
      option.checked = !option.checked;

      this.localFilters.violenceTypes = this.violenceTypeOptions
        .slice(1)
        .filter((opt) => opt.checked)
        .map((opt) => opt.value);

      if (this.localFilters.violenceTypes.length === 0) {
        this.violenceTypeOptions[0].checked = true;
        this.localFilters.violenceTypes = ['all'];
      }
    }
  }

  // Aplicar filtros
  applyFilters() {
    console.log('Aplicando filtros:', this.localFilters);
    this.filtersChanged.emit({ ...this.localFilters });
  }

  // Resetear filtros
  resetFilters() {
    this.localFilters = {
      startDate: '2000-01-01',
      endDate: '2024-12-31',
      region: 'all',
      violenceTypes: ['all'],
    };

    // Resetear checkboxes
    this.violenceTypeOptions.forEach((opt, index) => {
      opt.checked = index === 0;
    });

    this.filtersReset.emit();
    this.applyFilters();
  }
}
