import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ConflictSummary {
  event_id: string;
  conflict_name: string;
  type_of_violence: string;
  side_a: string;
  side_b: string;
  country: string;
  region: string;
  date_start: string;
  date_end: string;
  deaths_a: number;
  deaths_b: number;
  deaths_total: number;
  length_of_conflict: number;
}

export interface ConflictListResponse {
  total: number;
  conflicts: ConflictSummary[];
}

export interface CountryStats {
  country: string;
  total_events: number;
  total_deaths: number;
  conflicts: string[];
}

export interface StatsResponse {
  top_countries: CountryStats[];
  total_events: number;
  total_deaths: number;
}

@Injectable({
  providedIn: 'root',
})
export class BigqueryService {
  private baseUrl = `${environment.apiUrl}/bigquery`;

  constructor(private http: HttpClient) {}

  /**
   * Obtener lista de conflictos con paginación
   */
  getConflicts(
    limit: number = 100,
    offset: number = 0,
    country?: string,
    region?: string
  ): Observable<ConflictListResponse> {
    let params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());

    if (country) params = params.set('country', country);
    if (region) params = params.set('region', region);

    return this.http.get<ConflictListResponse>(`${this.baseUrl}/conflicts`, {
      params,
    });
  }

  /**
   * Obtener conflicto por ID
   */
  getConflictById(eventId: string): Observable<ConflictSummary> {
    return this.http.get<ConflictSummary>(
      `${this.baseUrl}/conflicts/${eventId}`
    );
  }

  /**
   * Obtener estadísticas generales
   */
  getStatistics(topCountries: number = 10): Observable<StatsResponse> {
    const params = new HttpParams().set(
      'top_countries',
      topCountries.toString()
    );
    return this.http.get<StatsResponse>(`${this.baseUrl}/stats`, { params });
  }

  /**
   * Buscar conflictos
   */
  searchConflicts(
    query: string,
    limit: number = 20
  ): Observable<ConflictSummary[]> {
    const params = new HttpParams()
      .set('q', query)
      .set('limit', limit.toString());

    return this.http.get<ConflictSummary[]>(`${this.baseUrl}/search`, {
      params,
    });
  }

  /**
   * Obtener top países
   */
  getTopCountries(limit: number = 10): Observable<CountryStats[]> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<CountryStats[]>(`${this.baseUrl}/countries/top`, {
      params,
    });
  }
}
