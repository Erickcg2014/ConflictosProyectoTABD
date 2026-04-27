import {
  Component,
  OnInit,
  Input,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  StatisticsService,
  DashboardStats,
} from '../../../../../../core/services/statistics.service';

interface StatCard {
  id: string;
  label: string;
  value: number;
  formattedValue: string;
  icon: string;
  trend: {
    value: number;
    direction: 'up' | 'down';
    label: string;
  };
  sparklineData: number[];
  color: string;
}

interface FilterState {
  startDate: string;
  endDate: string;
  region: string;
  violenceTypes: string[];
}

@Component({
  selector: 'app-stats-cards',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './stats-cards.component.html',
  styleUrls: ['./stats-cards.component.css'],
})
export class StatsCardsComponent implements OnInit, OnChanges {
  @Input() filters?: FilterState;

  cards: StatCard[] = [];
  loading = false;
  error: string | null = null;

  constructor(private statsService: StatisticsService) {}

  ngOnInit() {
    this.loadDataWithFilters();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['filters'] && !changes['filters'].firstChange) {
      console.log(
        '📊 Stats cards: Filters changed, reloading data...',
        this.filters
      );
      this.loadDataWithFilters();
    }
  }

  private loadDataWithFilters() {
    console.log('📡 Loading stats cards with filters:', this.filters);

    this.loading = true;
    this.error = null;

    // Preparar filtros para el servicio
    const serviceFilters = {
      start_date: this.filters?.startDate || '2020-01-01',
      end_date: this.filters?.endDate || '2024-12-31',
      region: this.filters?.region || 'all',
    };

    this.statsService.getDashboardStats(serviceFilters).subscribe({
      next: (data: DashboardStats) => {
        console.log('✅ Stats loaded successfully:', data);
        this.updateCardsFromBackend(data);
        this.loading = false;
      },
      error: (err) => {
        console.error('❌ Error loading stats:', err);
        this.error = 'Error al cargar las estadísticas';
        this.loading = false;
      },
    });
  }

  private updateCardsFromBackend(data: DashboardStats) {
    this.cards = [
      {
        id: 'events',
        label: 'Total de Eventos',
        value: data.total_events,
        formattedValue: this.formatNumber(data.total_events),
        icon: 'event',
        trend: {
          value: Math.abs(data.trends.events_change),
          direction: data.trends.events_change >= 0 ? 'up' : 'down',
          label: 'vs periodo anterior',
        },
        sparklineData: this.generateMockSparkline(
          data.total_events,
          data.trends.events_change
        ),
        color: '#3B82F6',
      },
      {
        id: 'deaths',
        label: 'Total de Muertes',
        value: data.total_deaths,
        formattedValue: this.formatNumber(data.total_deaths),
        icon: 'dangerous',
        trend: {
          value: Math.abs(data.trends.deaths_change),
          direction: data.trends.deaths_change >= 0 ? 'up' : 'down',
          label: 'vs periodo anterior',
        },
        sparklineData: this.generateMockSparkline(
          data.total_deaths,
          data.trends.deaths_change
        ),
        color: '#EF4444',
      },
      {
        id: 'countries',
        label: 'Países Afectados',
        value: data.countries_affected,
        formattedValue: this.formatNumber(data.countries_affected),
        icon: 'public',
        trend: {
          value: Math.abs(data.trends.countries_change),
          direction: data.trends.countries_change >= 0 ? 'up' : 'down',
          label: 'vs periodo anterior',
        },
        sparklineData: this.generateMockSparkline(
          data.countries_affected,
          data.trends.countries_change
        ),
        color: '#10B981',
      },
      {
        id: 'conflicts',
        label: 'Conflictos Únicos',
        value: data.unique_conflicts,
        formattedValue: this.formatNumber(data.unique_conflicts),
        icon: 'gavel',
        trend: {
          value: Math.abs(data.trends.conflicts_change),
          direction: data.trends.conflicts_change >= 0 ? 'up' : 'down',
          label: 'vs periodo anterior',
        },
        sparklineData: this.generateMockSparkline(
          data.unique_conflicts,
          data.trends.conflicts_change
        ),
        color: '#F59E0B',
      },
    ];
  }

  // Generar datos de sparkline basados en el valor final y la tendencia
  private generateMockSparkline(
    finalValue: number,
    trendPercent: number
  ): number[] {
    const points = 7;
    const data: number[] = [];
    const initialValue = finalValue / (1 + trendPercent / 100);
    const step = (finalValue - initialValue) / (points - 1);

    for (let i = 0; i < points; i++) {
      const value = initialValue + step * i;
      const variation = value * (Math.random() * 0.1 - 0.05);
      data.push(Math.round(value + variation));
    }

    return data;
  }

  // Formatear números grandes
  formatNumber(value: number): string {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(2) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(1) + 'K';
    }
    return value.toLocaleString();
  }

  // Generar path para el mini gráfico (sparkline)
  generateSparklinePath(data: number[]): string {
    if (data.length === 0) return '';

    const width = 100;
    const height = 30;
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }
}
