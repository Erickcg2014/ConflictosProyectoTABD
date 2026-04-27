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
  selector: 'app-violence-type-chart',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './violence-type-chart.component.html',
  styleUrls: ['./violence-type-chart.component.css'],
})
export class ViolenceTypeChartComponent
  implements OnInit, AfterViewInit, OnChanges
{
  @Input() filters?: FilterState;
  @ViewChild('chartContainer') chartContainer!: ElementRef;

  isVisible = false;
  isLoading = false;

  currentMetric: 'events' | 'deaths' = 'events';
  public readonly doughnutChartType = 'doughnut' as const;
  public doughnutChartData: ChartConfiguration<'doughnut'>['data'] = {
    labels: [],
    datasets: [
      {
        data: [],
        backgroundColor: [
          'rgba(249, 115, 22, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(234, 179, 8, 0.8)',
        ],
        borderColor: ['#F97316', '#A855F7', '#EAB308'],
        borderWidth: 2,
        hoverOffset: 15,
        hoverBorderWidth: 3,
      },
    ],
  };

  public doughnutChartOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,

    layout: {
      padding: 0,
    },

    plugins: {
      legend: {
        display: false,
      },

      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: {
          size: 14,
          weight: 'bold',
        },
        bodyFont: {
          size: 13,
        },
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: (ctx) => {
            const label = ctx.label || '';
            const val = ctx.parsed;
            const total = (ctx.dataset.data as number[]).reduce(
              (a, b) => a + b,
              0
            );
            const percentage =
              total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
            return `${label}: ${new Intl.NumberFormat('es-ES').format(
              val
            )} (${percentage}%)`;
          },
        },
      },
    },

    elements: {
      arc: {
        borderWidth: 2,
      },
    },
  };

  constructor(private statisticsService: StatisticsService) {}

  ngOnInit() {
    console.log('🔧 ViolenceTypeChart: Componente inicializado');
  }

  ngOnChanges(changes: SimpleChanges) {
    console.log('🔄 ViolenceTypeChart: Cambio detectado en inputs', changes);

    if (
      changes['filters'] &&
      !changes['filters'].firstChange &&
      this.isVisible
    ) {
      console.log('🔄 ViolenceTypeChart: Recargando datos con nuevos filtros');
      this.loadDataWithFilters();
    }
  }

  ngAfterViewInit() {
    console.log('👁️ ViolenceTypeChart: Configurando Intersection Observer');
    this.setupIntersectionObserver();
  }

  private setupIntersectionObserver() {
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !this.isVisible) {
          this.isVisible = true;
          this.loadDataWithFilters();
          obs.disconnect();
        }
      },
      { threshold: 0.15 }
    );

    obs.observe(this.chartContainer.nativeElement);
  }

  toggleMetric() {
    const newMetric = this.currentMetric === 'events' ? 'deaths' : 'events';
    console.log(
      `🔄 ViolenceTypeChart: Toggle métrica de ${this.currentMetric} → ${newMetric}`
    );
    this.currentMetric = newMetric;
    this.loadDataWithFilters();
  }

  private loadDataWithFilters() {
    if (!this.filters) {
      console.warn('⚠️ ViolenceTypeChart: No hay filtros disponibles');
      return;
    }

    console.log('📊 ViolenceTypeChart: Iniciando carga de datos');
    console.log('   Filtros:', this.filters);
    console.log('   Métrica actual:', this.currentMetric);

    this.isLoading = true;

    this.statisticsService
      .getViolenceTypes(this.filters, this.currentMetric)
      .subscribe({
        next: (resp) => {
          console.log('✅ ViolenceTypeChart: Respuesta recibida del backend');
          console.log('   Response completa:', resp);

          const labels = resp.types ?? [];
          const values = resp.values ?? [];

          console.log('   📊 Labels procesados:', labels);
          console.log('   📊 Values procesados:', values);
          console.log('   📊 Percentages:', resp.percentages);

          this.doughnutChartData.labels = labels;
          this.doughnutChartData.datasets[0].data = values;

          this.isLoading = false;
          console.log(
            '✅ ViolenceTypeChart: Gráfica actualizada correctamente'
          );
        },
        error: (err) => {
          console.error('❌ ViolenceTypeChart: Error al cargar datos', err);
          console.error('   Detalles del error:', {
            message: err.message,
            status: err.status,
            statusText: err.statusText,
            url: err.url,
            error: err.error,
          });
          this.isLoading = false;
        },
      });
  }

  getToggleLabel(): string {
    return this.currentMetric === 'events'
      ? 'Ver por Muertes'
      : 'Ver por Eventos';
  }

  formatNumber(value: number): string {
    return new Intl.NumberFormat('es-ES').format(value);
  }

  /**
   * Calcula el total sumando todos los valores dinámicamente
   */
  getTotalValue(): number {
    const data = (this.doughnutChartData.datasets[0].data as number[]) || [];
    return data.reduce((acc, val) => acc + (val || 0), 0);
  }

  /**
   * Obtiene los datos actuales formateados
   */
  getCurrentData() {
    const labels = (this.doughnutChartData.labels as string[]) || [];
    const data = (this.doughnutChartData.datasets[0].data as number[]) || [];

    const total = data.reduce((a, b) => a + (b || 0), 0) || 1;
    const percentages = data.map((v) => ((v / total) * 100).toFixed(1));

    return {
      title:
        this.currentMetric === 'events'
          ? 'Distribución por Tipo de Violencia (Eventos)'
          : 'Distribución por Tipo de Violencia (Muertes)',
      labels,
      data,
      percentages,
    };
  }

  getColor(i: number): string {
    const colors = this.doughnutChartData.datasets[0]
      .backgroundColor as string[];
    return colors?.[i] ?? '#999';
  }
}
