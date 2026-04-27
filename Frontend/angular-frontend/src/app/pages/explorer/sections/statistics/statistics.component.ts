import { Component, OnInit, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { StatsFiltersComponent } from './components/stats-filters/stats-filters.component';
import { StatsCardsComponent } from './components/stats-cards/stats-cards.component';
import { TimelineChartComponent } from './components/timeline-chart/timeline-chart.component';
import { TopCountriesChartComponent } from './components/top-countries-chart/top-countries-chart.component';
import { ViolenceTypeChartComponent } from './components/violence-type-chart/violence-type-chart.component';
import { ConflictsTableComponent } from './components/conflicts-table/conflicts-table.component';

// Interfaces
interface FilterState {
  startDate: string;
  endDate: string;
  region: string;
  violenceTypes: string[];
}

interface NavigationSection {
  id: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-statistics',
  standalone: true,
  imports: [
    CommonModule,
    StatsFiltersComponent,
    StatsCardsComponent,
    TimelineChartComponent,
    TopCountriesChartComponent,
    ViolenceTypeChartComponent,
    ConflictsTableComponent,
  ],
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.css'],
})
export class StatisticsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  showScrollTop = false;

  isLoadingData = false;

  currentFilters: FilterState = {
    startDate: '2000-01-01',
    endDate: '2024-12-31',
    region: 'all',
    violenceTypes: ['all'],
  };

  activeSection = 'section-cards';

  sections: NavigationSection[] = [
    { id: 'section-cards', label: 'Métricas', icon: 'dashboard' },
    { id: 'section-timeline', label: 'Evolución', icon: 'show_chart' },
    { id: 'section-analysis', label: 'Análisis', icon: 'pie_chart' },
    { id: 'section-table', label: 'Tabla', icon: 'table_chart' },
  ];

  private scrollTimeout: any;

  ngOnInit() {
    console.log('📊 Statistics component initialized');
    this.loadInitialData();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();

    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout);
    }
  }

  private loadInitialData() {
    console.log('📡 Loading initial statistics data...');
  }

  @HostListener('window:scroll', [])
  onScroll() {
    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout);
    }

    this.scrollTimeout = setTimeout(() => {
      const scrollPos = window.pageYOffset;
      this.showScrollTop = scrollPos > 400;

      this.updateActiveSection();
    }, 100);
  }

  private updateActiveSection() {
    const scrollPosition = window.pageYOffset + 250;

    for (const section of this.sections) {
      const element = document.getElementById(section.id);
      if (element) {
        const offsetTop = element.offsetTop;
        const offsetBottom = offsetTop + element.offsetHeight;

        if (scrollPosition >= offsetTop && scrollPosition < offsetBottom) {
          if (this.activeSection !== section.id) {
            this.activeSection = section.id;
            console.log('📍 Active section:', section.label);
          }
          break;
        }
      }
    }
  }

  // Scroll a sección específica
  scrollToSection(sectionId: string) {
    const element = document.getElementById(sectionId);
    if (!element) {
      console.warn(`⚠️ Section ${sectionId} not found`);
      return;
    }

    const headerOffset = 180;
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth',
    });

    this.activeSection = sectionId;
  }

  scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });

    this.activeSection = this.sections[0].id;
  }

  // Recibir cambios de filtros
  onFiltersChanged(filters: FilterState) {
    console.log('🔄 Filters updated:', filters);

    if (new Date(filters.startDate) > new Date(filters.endDate)) {
      console.error('❌ Start date cannot be after end date');
      return;
    }

    this.currentFilters = { ...filters };
    this.applyFilters();
  }

  // Aplicar filtros (llamar backend)
  private applyFilters() {
    this.isLoadingData = true;
    console.log('📡 Applying filters:', this.currentFilters);
    setTimeout(() => {
      this.isLoadingData = false;
      console.log('✅ Filters applied successfully');
    }, 500);
  }

  // Resetear filtros
  onFiltersReset() {
    console.log('🔄 Filters reset to default');

    this.currentFilters = {
      startDate: '2000-01-01',
      endDate: '2024-12-31',
      region: 'all',
      violenceTypes: ['all'],
    };

    this.applyFilters();
  }

  exportAllData() {
    console.log('📥 Exporting all statistics data...');
  }

  shareCurrentView() {
    console.log('🔗 Sharing current view...');
  }
}
