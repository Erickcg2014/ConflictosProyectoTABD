import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface GeoLocation {
  type: string;
  coordinates: [number, number]; // [longitude, latitude]
}

export interface WarLocation {
  event_id: string;
  conflict_name: string;
  country: string;
  region: string;
  location: GeoLocation;
}

export interface ClusterData {
  _id: any;
  longitude: number;
  latitude: number;
  count: number;
  event_ids: string[];
  conflicts: string[];
  countries: string[];
}

export interface GeoSearchResponse {
  results: WarLocation[];
  count: number;
  search_center: {
    longitude: number;
    latitude: number;
  };
}

@Injectable({
  providedIn: 'root',
})
export class MongodbService {
  private baseUrl = `${environment.apiUrl}/mongodb`;

  constructor(private http: HttpClient) {}

  /**
   * Buscar eventos cercanos a una ubicación
   */
  searchNearby(
    longitude: number,
    latitude: number,
    maxDistanceKm: number = 100,
    limit: number = 10
  ): Observable<GeoSearchResponse> {
    const params = new HttpParams()
      .set('longitude', longitude.toString())
      .set('latitude', latitude.toString())
      .set('max_distance_km', maxDistanceKm.toString())
      .set('limit', limit.toString());

    return this.http.get<GeoSearchResponse>(`${this.baseUrl}/geo/nearby`, {
      params,
    });
  }

  /**
   * Obtener eventos dentro de un bounding box
   */
  getLocationsInBounds(
    minLon: number,
    minLat: number,
    maxLon: number,
    maxLat: number,
    limit: number = 500
  ): Observable<WarLocation[]> {
    const params = new HttpParams()
      .set('min_lon', minLon.toString())
      .set('min_lat', minLat.toString())
      .set('max_lon', maxLon.toString())
      .set('max_lat', maxLat.toString())
      .set('limit', limit.toString());

    return this.http.get<WarLocation[]>(`${this.baseUrl}/geo/bounds`, {
      params,
    });
  }

  /**
   * Obtener datos agregados para clustering
   */
  getMapClusters(
    zoom: number,
    bounds?: {
      min_lon: number;
      min_lat: number;
      max_lon: number;
      max_lat: number;
    }
  ): Observable<ClusterData[]> {
    let params = new HttpParams().set('zoom', zoom.toString());

    if (bounds) {
      params = params
        .set('min_lon', bounds.min_lon.toString())
        .set('min_lat', bounds.min_lat.toString())
        .set('max_lon', bounds.max_lon.toString())
        .set('max_lat', bounds.max_lat.toString());
    }

    return this.http.get<ClusterData[]>(`${this.baseUrl}/geo/clusters`, {
      params,
    });
  }

  /**
   * Obtener ubicación por event_id
   */
  getLocationByEventId(eventId: string): Observable<WarLocation> {
    return this.http.get<WarLocation>(`${this.baseUrl}/events/${eventId}`);
  }

  /**
   * Obtener múltiples ubicaciones por event_ids
   */
  getLocationsBatch(eventIds: string[]): Observable<WarLocation[]> {
    return this.http.post<WarLocation[]>(
      `${this.baseUrl}/events/batch`,
      eventIds
    );
  }

  /**
   * Buscar por país
   */
  searchByCountry(
    country: string,
    limit: number = 100
  ): Observable<WarLocation[]> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<WarLocation[]>(`${this.baseUrl}/country/${country}`, {
      params,
    });
  }

  /**
   * Obtener lista de países
   */
  getCountries(): Observable<string[]> {
    return this.http.get<string[]>(`${this.baseUrl}/countries`);
  }

  /**
   * Obtener estadísticas
   */
  getLocationCount(): Observable<{ total_locations: number }> {
    return this.http.get<{ total_locations: number }>(
      `${this.baseUrl}/stats/count`
    );
  }
}
