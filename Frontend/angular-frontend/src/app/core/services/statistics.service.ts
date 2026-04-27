// src/app/core/services/statistics.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { tap } from 'rxjs/operators';

// ===== Interfaces =====
export interface DashboardStats {
  total_events: number;
  total_deaths: number;
  countries_affected: number;
  unique_conflicts: number;
  trends: {
    events_change: number;
    deaths_change: number;
    countries_change: number;
    conflicts_change: number;
  };
}

export interface ViolenceTypesResponse {
  types: string[];
  values: number[];
  percentages: number[];
  metric: 'events' | 'deaths';
}

export interface TimelineYear {
  year: number;
  events: number;
}

export interface TimelineResponse {
  labels: string[];
  events: number[];
  deaths: number[];
  granularity: string;
}

export interface StatsFilters {
  start_date?: string;
  end_date?: string;
  region?: string;
}

// --- Filters Interfaces ---
export interface RegionOption {
  value: string;
  label: string;
  count: number;
}

export interface ViolenceTypeOption {
  value: string;
  label: string;
  count: number;
}

export interface DateRange {
  min_date: string;
  max_date: string;
  total_years: number;
}

export interface FiltersMetadata {
  regions: RegionOption[];
  violence_types: ViolenceTypeOption[];
  date_range: DateRange;
}

@Injectable({
  providedIn: 'root',
})
export class StatisticsService {
  private apiUrl = `${environment.apiUrl}/statistics`;

  constructor(private http: HttpClient) {}

  /**
   * Limpia parámetros null/undefined
   */
  private cleanParams(params: any): any {
    const cleaned = { ...params };

    Object.keys(cleaned).forEach((key) => {
      if (cleaned[key] === null || cleaned[key] === undefined) {
        delete cleaned[key];
      }
    });

    return cleaned;
  }

  // =======================
  // Dashboard Summary
  // =======================
  getDashboardStats(filters: StatsFilters): Observable<DashboardStats> {
    let params: any = {
      start_date: filters.start_date,
      end_date: filters.end_date,
      region: filters.region,
    };

    params = this.cleanParams(params);

    return this.http.get<DashboardStats>(`${this.apiUrl}/dashboard`, {
      params,
    });
  }

  // =======================
  // Filters Endpoints
  // =======================
  getRegions(): Observable<{ regions: RegionOption[] }> {
    return this.http.get<{ regions: RegionOption[] }>(
      `${this.apiUrl}/filters/regions`
    );
  }

  getViolenceTypes(
    filters: any,
    metric: 'events' | 'deaths'
  ): Observable<ViolenceTypesResponse> {
    const params = this.cleanParams({
      start_date: filters.startDate,
      end_date: filters.endDate,
      region: filters.region || 'all',
      metric,
    });

    const queryString = new URLSearchParams(params).toString();
    const fullUrl = `${this.apiUrl}/violence-types?${queryString}`;

    console.log('🌐 Violence Types Request URL:', fullUrl);
    console.log('📊 Violence Types Request Params:', params);

    return this.http
      .get<ViolenceTypesResponse>(`${this.apiUrl}/violence-types`, { params })
      .pipe(
        tap((response) => {
          console.log('✅ Violence Types API Response:', response);
        })
      );
  }

  getDateRange(): Observable<{ date_range: DateRange }> {
    return this.http.get<{ date_range: DateRange }>(
      `${this.apiUrl}/filters/date-range`
    );
  }

  getFiltersMetadata(): Observable<FiltersMetadata> {
    return this.http.get<FiltersMetadata>(`${this.apiUrl}/filters/metadata`);
  }

  // =======================
  // Timeline
  // =======================
  getTimeline(filters: any): Observable<TimelineResponse> {
    let params: any = {
      start_date: filters.startDate,
      end_date: filters.endDate,
      region: filters.region || 'all',
      granularity: filters.granularity || 'year',
    };

    if (
      filters.violenceTypes &&
      filters.violenceTypes.length > 0 &&
      filters.violenceTypes[0] !== 'all'
    ) {
      params.violence_types = filters.violenceTypes;
    }

    params = this.cleanParams(params);

    const queryString = new URLSearchParams(params).toString();
    const fullUrl = `${this.apiUrl}/timeline?${queryString}`;
    console.log('🌐 Timeline Request URL:', fullUrl);

    return this.http
      .get<TimelineResponse>(`${this.apiUrl}/timeline`, { params })
      .pipe(
        tap((response) => {
          console.log('Timeline API Response:', response);
        })
      );
  }

  // =======================
  // Top Countries
  // =======================
  getTopCountries(filters: any, metric: 'events' | 'deaths') {
    let params: any = {
      start_date: filters.startDate,
      end_date: filters.endDate,
      region: filters.region || 'all',
      metric,
      limit: 10,
    };

    params = this.cleanParams(params);

    const queryString = new URLSearchParams(params).toString();
    const fullUrl = `${this.apiUrl}/top-countries?${queryString}`;
    console.log('🌐 Top Countries Request URL:', fullUrl);

    return this.http.get(`${this.apiUrl}/top-countries`, { params }).pipe(
      tap((response) => {
        console.log('Top Countries API Response:', response);
      })
    );
  }

  // =======================
  // Conflicts Table
  // =======================
  getConflictsTable(
    filters: any,
    page: number,
    pageSize: number,
    sortBy: string,
    sortOrder: string,
    search: string = ''
  ) {
    let params: any = {
      start_date: filters.startDate,
      end_date: filters.endDate,
      region: filters.region ?? 'all',
      sort_by: sortBy,
      sort_order: sortOrder,
      limit: pageSize,
      offset: (page - 1) * pageSize,
      search: search?.trim() || null,
    };

    params = this.cleanParams(params);

    return this.http.get<any>(`${this.apiUrl}/conflicts`, {
      params,
    });
  }
}
