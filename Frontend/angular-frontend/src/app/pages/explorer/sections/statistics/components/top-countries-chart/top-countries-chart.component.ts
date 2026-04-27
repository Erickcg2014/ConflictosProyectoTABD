import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewInit,
  Input,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartType } from 'chart.js';
import { StatisticsService } from '../../../../../../core/services/statistics.service';

interface FilterState {
  startDate: string;
  endDate: string;
  region: string;
  violenceTypes: string[];
}

@Component({
  selector: 'app-top-countries-chart',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './top-countries-chart.component.html',
  styleUrls: ['./top-countries-chart.component.css'],
})
export class TopCountriesChartComponent
  implements OnInit, AfterViewInit, OnChanges
{
  @ViewChild('chartContainer') chartContainer!: ElementRef;
  @Input() filters?: FilterState;

  isVisible = false;
  isLoading = false;

  currentMetric: 'events' | 'deaths' = 'events';
  public barChartType: ChartType = 'bar';

  public barChartData: ChartConfiguration['data'] = {
    labels: [],
    datasets: [
      {
        data: [],
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(132, 204, 22, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(20, 184, 166, 0.8)',
          'rgba(6, 182, 212, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(99, 102, 241, 0.8)',
        ],
        borderColor: [
          '#EF4444',
          '#F97316',
          '#F59E0B',
          '#EAB308',
          '#84CC16',
          '#22C55E',
          '#14B8A6',
          '#06B6D4',
          '#3B82F6',
          '#6366F1',
        ],
        borderWidth: 2,
        borderRadius: 6,
        barThickness: 40,
        maxBarThickness: 50,
        label: 'Top Países',
      },
    ],
  };

  public barChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        callbacks: {
          label: (ctx: any) => {
            const v = ctx.parsed.x;
            return new Intl.NumberFormat('es-ES').format(v ?? 0);
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          callback: (value: any) => {
            const n = Number(value);
            return Number.isFinite(n)
              ? new Intl.NumberFormat('es-ES', {
                  notation: 'compact',
                  compactDisplay: 'short',
                }).format(n)
              : '';
          },
        },
      },
      y: { ticks: { font: { size: 12, weight: 600 } } },
    },
  };

  constructor(private statisticsService: StatisticsService) {}

  ngOnInit() {}

  ngAfterViewInit() {
    this.setupIntersectionObserver();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['filters'] && this.filters) {
      if (this.isVisible) {
        this.loadDataWithFilters();
      } else {
        this.isVisible = true;
        setTimeout(() => this.loadDataWithFilters(), 50);
      }
    }
  }

  toggleMetric() {
    this.currentMetric = this.currentMetric === 'events' ? 'deaths' : 'events';
    this.loadDataWithFilters();
  }

  private setupIntersectionObserver() {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !this.isVisible) {
          this.isVisible = true;
          setTimeout(() => this.loadDataWithFilters(), 60);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    setTimeout(() => {
      if (this.chartContainer?.nativeElement) {
        observer.observe(this.chartContainer.nativeElement);
      }
    }, 100);
  }

  private loadDataWithFilters() {
    if (!this.filters) return;

    this.isLoading = true;

    this.statisticsService
      .getTopCountries(this.filters, this.currentMetric)
      .subscribe({
        next: (resp: any) => {
          console.log('✅ Top Countries Backend Response:', resp);
          const labels = resp.countries ?? [];
          const data = resp.values ?? [];

          this.barChartData.labels = labels;
          this.barChartData.datasets[0].data = data;
          this.barChartData.datasets[0].label =
            this.currentMetric === 'events' ? 'Eventos' : 'Muertes';

          this.isLoading = false;
        },
        error: (err) => {
          console.error('❌ Error loading top countries:', err);
          this.isLoading = false;
        },
      });
  }

  getToggleLabel(): string {
    return this.currentMetric === 'events'
      ? 'Ver por Muertes'
      : 'Ver por Eventos';
  }
}
