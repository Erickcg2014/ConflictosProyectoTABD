import {
  Component,
  Input,
  OnChanges,
  SimpleChanges,
  ViewChild,
  ElementRef,
  AfterViewInit,
} from '@angular/core';
import { ChartData, ChartOptions } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import { DecimalPipe, CommonModule } from '@angular/common';
import { StatisticsService } from '../../../../../../core/services/statistics.service';

interface Insights {
  maxYear: number;
  maxDeaths: number;
  trend: string;
  recentYears: number;
  minDeaths: number;
  peaceYear: number;
}

@Component({
  selector: 'app-timeline-chart',
  standalone: true,
  imports: [CommonModule, BaseChartDirective, DecimalPipe],
  templateUrl: './timeline-chart.component.html',
  styleUrls: ['./timeline-chart.component.css'],
})
export class TimelineChartComponent implements OnChanges, AfterViewInit {
  @Input() filters: any;
  @ViewChild('chartContainer') chartContainer!: ElementRef;
  @ViewChild(BaseChartDirective) chart!: BaseChartDirective;

  lineChartType: any = 'line';

  lineChartData: ChartData<'line'> = { labels: [], datasets: [] };

  lineChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    scales: {
      y: { beginAtZero: true, title: { display: true, text: 'Muertes' } },
      y1: {
        beginAtZero: true,
        position: 'right',
        title: { display: true, text: 'Eventos' },
        grid: { drawOnChartArea: false },
      },
    },
  };

  insights!: Insights;
  isLoaded = false;
  isLoading = false;
  isVisible = false;

  constructor(private statisticsService: StatisticsService) {}

  ngAfterViewInit() {
    this.initLazyLoad();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['filters'] && this.filters) {
      if (this.isVisible) {
        this.loadData();
      } else {
        this.isVisible = true;
        this.loadData();
      }
    }
  }

  private initLazyLoad() {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !this.isVisible) {
        this.isVisible = true;
        this.loadData();
        observer.disconnect();
      }
    });

    observer.observe(this.chartContainer.nativeElement);
  }

  private loadData() {
    if (!this.filters) return;
    this.isLoading = true;

    this.statisticsService.getTimeline(this.filters).subscribe({
      next: (data) => {
        console.log('✅ Timeline Response:', data);

        const timeline = data.labels.map((label: string, i: number) => ({
          period: label,
          total_deaths: data.deaths[i],
          total_events: data.events[i],
        }));

        this.updateChart(timeline);
        this.extractInsights(timeline);

        this.isLoaded = true;
        this.isLoading = false;
        this.chart?.update();
      },
      error: (err) => {
        console.error('❌ Error loading timeline', err);
        this.isLoading = false;
      },
    });
  }

  private updateChart(timeline: any[]) {
    const labels = timeline.map((d) => d.period);
    const deaths = timeline.map((d) => d.total_deaths);
    const events = timeline.map((d) => d.total_events);

    this.lineChartData = {
      labels,
      datasets: [
        {
          label: 'Total de Muertes',
          data: deaths,
          borderColor: '#EF4444',
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          fill: true,
          tension: 0.35,
          pointRadius: 3,
        },
        {
          label: 'Eventos',
          data: events,
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          fill: true,
          tension: 0.35,
          pointRadius: 3,
          yAxisID: 'y1',
        },
      ],
    };
  }

  private extractInsights(data: any[]) {
    const sorted = [...data];
    const max = sorted.reduce((a, b) =>
      b.total_deaths > a.total_deaths ? b : a
    );
    const min = sorted.reduce((a, b) =>
      b.total_deaths < a.total_deaths ? b : a
    );
    const first = sorted[0];
    const last = sorted[sorted.length - 1];

    this.insights = {
      maxYear: max.period,
      maxDeaths: max.total_deaths,
      peaceYear: min.period,
      minDeaths: min.total_deaths,
      trend: last.total_deaths > first.total_deaths ? 'Aumento' : 'Reducción',
      recentYears: Math.min(sorted.length, 5),
    };
  }
}
