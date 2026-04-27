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
import { FormsModule } from '@angular/forms';
import { StatisticsService } from '../../../../../../core/services/statistics.service';

interface FilterState {
  startDate: string;
  endDate: string;
  region: string;
  violenceTypes: string[];
}

interface Conflict {
  id: number;
  name: string;
  countries: string;
  actors: string;
  events: number;
  deaths: number;
  period: string;
  region: string;
}

type SortColumn = 'name' | 'events' | 'deaths' | 'period';
type SortDirection = 'asc' | 'desc';

@Component({
  selector: 'app-conflicts-table',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './conflicts-table.component.html',
  styleUrls: ['./conflicts-table.component.css'],
})
export class ConflictsTableComponent
  implements OnInit, AfterViewInit, OnChanges
{
  @ViewChild('tableContainer') tableContainer!: ElementRef;
  @Input() filters?: FilterState;

  constructor(private statisticsService: StatisticsService) {}

  Math = Math;
  isVisible = false;
  isLoading = false;

  // Datos cargados desde backend
  allConflicts: Conflict[] = [];
  filteredConflicts: Conflict[] = [];
  displayedConflicts: Conflict[] = [];

  // Paginación
  currentPage = 1;
  pageSize = 10;
  pageSizeOptions = [5, 10, 20, 50];
  totalPages = 1;
  totalRecords = 0;

  // Ordenamiento
  sortColumn: SortColumn = 'deaths';
  sortDirection: SortDirection = 'desc';

  // Búsqueda
  searchTerm = '';

  ngOnInit() {
    this.loadDataFromBackend();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (
      changes['filters'] &&
      !changes['filters'].firstChange &&
      this.isVisible
    ) {
      console.log('📋 Conflicts table: filters changed', this.filters);
      this.currentPage = 1;
      this.loadDataFromBackend();
    }
  }

  // Llamar backend
  private loadDataFromBackend() {
    if (!this.filters) return;

    this.isLoading = true;
    console.log(
      '📡 Loading conflicts from backend with filters:',
      this.filters
    );

    this.statisticsService
      .getConflictsTable(
        this.filters,
        this.currentPage,
        this.pageSize,
        this.sortColumn,
        this.sortDirection,
        this.searchTerm
      )
      .subscribe({
        next: (res) => {
          console.log('Backend response:', res);

          this.allConflicts = res.conflicts ?? [];
          this.totalRecords = res.total ?? this.allConflicts.length;

          console.log('Loaded conflicts (current page):', this.allConflicts);

          this.displayedConflicts = [...this.allConflicts];

          this.totalPages = Math.ceil(this.totalRecords / this.pageSize);

          this.isLoading = false;
        },

        error: (err) => {
          console.error('❌ Error loading conflicts', err);
          this.isLoading = false;
        },
      });
  }

  ngAfterViewInit() {
    this.setupIntersectionObserver();
  }

  // Lazy Loading
  private setupIntersectionObserver() {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !this.isVisible) {
            this.isVisible = true;
            this.loadDataFromBackend();
            observer.disconnect();
          }
        });
      },
      { root: null, rootMargin: '100px', threshold: 0.1 }
    );

    if (this.tableContainer) {
      observer.observe(this.tableContainer.nativeElement);
    }
  }

  // Búsqueda
  onSearch() {
    this.currentPage = 1;
    this.loadDataFromBackend();
  }

  clearSearch() {
    this.searchTerm = '';
    this.onSearch();
  }

  // Ordenamiento
  sortBy(column: SortColumn) {
    if (this.sortColumn === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = column;
      this.sortDirection = 'desc';
    }
    this.currentPage = 1;
    this.loadDataFromBackend();
  }

  getSortIcon(column: SortColumn): string {
    if (this.sortColumn !== column) return 'unfold_more';
    return this.sortDirection === 'asc' ? 'arrow_upward' : 'arrow_downward';
  }

  // Paginación
  onPageSizeChange() {
    this.currentPage = 1;
    this.loadDataFromBackend();
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadDataFromBackend();
    }
  }

  previousPage() {
    this.goToPage(this.currentPage - 1);
  }

  nextPage() {
    this.goToPage(this.currentPage + 1);
  }

  private updatePagination() {
    this.totalPages = Math.ceil(this.totalRecords / this.pageSize);
    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.displayedConflicts = this.filteredConflicts.slice(
      startIndex,
      endIndex
    );
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;

    let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(this.totalPages, start + maxVisible - 1);

    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }
    for (let i = start; i <= end; i++) pages.push(i);
    return pages;
  }

  // Utils
  formatNumber(value: number): string {
    return new Intl.NumberFormat('es-ES').format(value);
  }

  viewDetails(conflict: Conflict) {
    console.log('Detalles:', conflict);
  }

  exportData() {
    console.log('Exportando...');
  }
}
