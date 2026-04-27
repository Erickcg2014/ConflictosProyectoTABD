import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

// ======================================================
// INTERFACES
// ======================================================

export enum GraphFilterType {
  COUNTRY = 'country',
  ACTOR = 'actor',
}

export interface FilterItem {
  value: string;
  label: string;
  conflict_count: number;
  total_deaths: number;
}

export interface FiltersResponse {
  type: GraphFilterType;
  count: number;
  items: FilterItem[];
}

export interface NodeMetrics {
  total_conflicts: number;
  total_deaths: number;
  connections: number;
  total_events?: number;
  encounter_count?: number;
  countries_active?: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  region?: string;
  metrics: NodeMetrics;
}

export interface EdgeMetrics {
  event_count?: number;
  conflict_names?: string[];
  actors_involved?: string[];
  encounter_count?: number;
  via_conflict?: string;
  total_length?: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  weight: number;
  metrics: EdgeMetrics;
}

export interface GraphSummary {
  total_nodes: number;
  total_edges: number;
  total_deaths: number;
  total_conflicts: number;
  depth: number;
}

export interface GraphResponse {
  center_node: GraphNode;
  nodes: GraphNode[];
  edges: GraphEdge[];
  summary: GraphSummary;
}

export interface ConflictSummary {
  name: string;
  deaths: number;
  events?: number;
  encounters?: number;
  duration_days?: number;
}

export interface ConnectedEntity {
  name: string;
  shared_conflicts?: number;
  shared_deaths?: number;
  encounters?: number;
  deaths?: number;
  conflict_count?: number;
}

export interface ActorParticipation {
  name: string;
  participation_count: number;
  deaths_caused: number;
  role?: string;
}

export interface NodeStatistics {
  total_conflicts: number;
  total_deaths: number;
  total_events?: number;
  total_encounters?: number;
  connections: number;
  countries_active?: number;
}

export interface NodeDetails {
  type: string;
  name: string;
  region?: string;
  statistics: NodeStatistics;
  top_conflicts: ConflictSummary[];
  connected_entities: ConnectedEntity[];
  actors_involved?: ActorParticipation[];
}

export interface HealthCheckResponse {
  status: string;
  neo4j_connected: boolean;
  data_available: boolean;
  message: string;
}

// ======================================================
// SERVICIO
// ======================================================

@Injectable({
  providedIn: 'root',
})
export class ConflictMapService {
  private apiUrl = `${environment.apiUrl}/graph`;

  constructor(private http: HttpClient) {}

  /**
   * Obtiene lista de países o actores disponibles para filtro inicial
   *
   * @param type Tipo de filtro: 'country' o 'actor'
   * @param search Término de búsqueda opcional
   * @returns Observable con lista de filtros
   *
   * @example
   * this.service.getFilters('country').subscribe(filters => {
   *   console.log(filters.items); // [{value: "Afghanistan", ...}, ...]
   * });
   */
  getFilters(
    type: GraphFilterType,
    search?: string
  ): Observable<FiltersResponse> {
    let params = new HttpParams().set('type', type);

    if (search && search.trim().length >= 2) {
      params = params.set('search', search.trim());
    }

    return this.http.get<FiltersResponse>(`${this.apiUrl}/filters`, { params });
  }

  /**
   * Construye y obtiene la estructura del grafo para una entidad específica
   *
   * @param type Tipo de entidad: 'country' o 'actor'
   * @param value Nombre de la entidad
   * @param depth Profundidad del grafo (1 o 2)
   * @returns Observable con estructura completa del grafo
   *
   * @example
   * this.service.getGraphNodes('country', 'Afghanistan', 1).subscribe(graph => {
   *   console.log(graph.center_node);
   *   console.log(graph.nodes);
   *   console.log(graph.edges);
   * });
   */
  getGraphNodes(
    type: GraphFilterType,
    value: string,
    depth: number = 1
  ): Observable<GraphResponse> {
    const params = new HttpParams()
      .set('type', type)
      .set('value', value)
      .set('depth', depth.toString());

    return this.http.get<GraphResponse>(`${this.apiUrl}/nodes`, { params });
  }

  /**
   * Obtiene información detallada de un nodo específico
   *
   * @param type Tipo de nodo: 'country' o 'actor'
   * @param value Nombre del nodo
   * @returns Observable con detalles completos del nodo
   *
   * @example
   * this.service.getNodeDetails('country', 'Afghanistan').subscribe(details => {
   *   console.log(details.statistics);
   *   console.log(details.top_conflicts);
   *   console.log(details.connected_entities);
   * });
   */
  getNodeDetails(
    type: GraphFilterType,
    value: string
  ): Observable<NodeDetails> {
    const params = new HttpParams().set('type', type).set('value', value);

    return this.http.get<NodeDetails>(`${this.apiUrl}/node-details`, {
      params,
    });
  }

  /**
   * Verifica el estado de salud del servicio de grafo
   *
   * @returns Observable con estado del servicio
   *
   * @example
   * this.service.healthCheck().subscribe(health => {
   *   if (health.neo4j_connected && health.data_available) {
   *     console.log('Service is healthy');
   *   }
   * });
   */
  healthCheck(): Observable<HealthCheckResponse> {
    return this.http.get<HealthCheckResponse>(`${this.apiUrl}/health`);
  }

  /**
   * Formatea número con separadores de miles
   *
   * @param value Número a formatear
   * @returns String formateado (ej: "50,000")
   */
  formatNumber(value: number): string {
    return value.toLocaleString('en-US');
  }

  /**
   * Obtiene color basado en intensidad de muertes
   * Usado para colorear nodos en el grafo
   *
   * @param deaths Número de muertes
   * @param maxDeaths Máximo de muertes en el grafo
   * @returns Color HEX
   *
   * @example
   * const color = this.service.getColorByIntensity(5000, 50000);
   * // Retorna un tono de rojo proporcional
   */
  getColorByIntensity(deaths: number, maxDeaths: number): string {
    if (maxDeaths === 0) return '#ccc';

    const intensity = deaths / maxDeaths;

    // Escala de colores: amarillo → naranja → rojo
    if (intensity < 0.3) {
      return '#ffd700'; // Amarillo (bajo)
    } else if (intensity < 0.6) {
      return '#ff8c00'; // Naranja (medio)
    } else {
      return '#dc143c'; // Rojo (alto)
    }
  }

  /**
   * Calcula tamaño de nodo basado en número de conexiones
   *
   * @param connections Número de conexiones del nodo
   * @param maxConnections Máximo de conexiones en el grafo
   * @param minSize Tamaño mínimo
   * @param maxSize Tamaño máximo
   * @returns Tamaño del nodo
   */
  getNodeSize(
    connections: number,
    maxConnections: number,
    minSize: number = 20,
    maxSize: number = 60
  ): number {
    if (maxConnections === 0) return minSize;

    const ratio = connections / maxConnections;
    return minSize + ratio * (maxSize - minSize);
  }

  /**
   * Calcula grosor de arista basado en peso
   *
   * @param weight Peso de la arista (muertes)
   * @param maxWeight Máximo peso en el grafo
   * @param minWidth Grosor mínimo
   * @param maxWidth Grosor máximo
   * @returns Grosor de la línea
   */
  getEdgeWidth(
    weight: number,
    maxWeight: number,
    minWidth: number = 1,
    maxWidth: number = 10
  ): number {
    if (maxWeight === 0) return minWidth;

    const ratio = weight / maxWeight;
    return minWidth + ratio * (maxWidth - minWidth);
  }
}
