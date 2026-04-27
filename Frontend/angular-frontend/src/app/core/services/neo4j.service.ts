import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

// ===============================
// Interfaces
// ===============================

export interface ActorRelationship {
  conflict: string;
  role: string;
  cumulative_deaths: number;
  event_count: number;
}

export interface ActorDetail {
  name: string;
  conflicts: ActorRelationship[];
  engaged_actors: string[];
  total_conflicts: number;
}

export interface ConflictNode {
  name: string;
  type_of_violence?: string;
  country?: string;
  region?: string;
  event_count?: number;
  total_deaths?: number;
  event_ids: string[];
}

export interface ActorNode {
  name: string;
  role?: string;
  cumulative_deaths?: number;
  event_count?: number;
}

export interface ActorNetwork {
  central_actor: string;
  related_actors: string[];
  network_size: number;
}

export interface ActorEngagement {
  conflict: string;
  total_deaths: number;
  total_length: number;
  encounter_count: number;
}

export interface TopActor {
  name: string;
  total_deaths: number;
  conflict_count: number;
}

export interface GraphStats {
  total_conflicts: number;
  total_actors: number;
  total_participations: number;
  total_engagements: number;
}

@Injectable({
  providedIn: 'root',
})
export class Neo4jService {
  private baseUrl = `${environment.apiUrl}/neo4j`;

  constructor(private http: HttpClient) {}

  /**
   * Obtener detalle de un actor con sus relaciones
   */
  getActorByName(actorName: string): Observable<ActorDetail> {
    return this.http.get<ActorDetail>(`${this.baseUrl}/actors/${actorName}`);
  }

  /**
   * Obtener información de un conflicto
   */
  getConflictByName(conflictName: string): Observable<ConflictNode> {
    return this.http.get<ConflictNode>(
      `${this.baseUrl}/conflicts/${conflictName}`
    );
  }

  /**
   * Obtener event_ids de un conflicto
   */
  getConflictEventIds(conflictName: string): Observable<string[]> {
    return this.http.get<string[]>(
      `${this.baseUrl}/conflicts/${conflictName}/event-ids`
    );
  }

  /**
   * Obtener actores involucrados en un conflicto
   */
  getConflictActors(conflictName: string): Observable<{
    conflict: ConflictNode;
    actors: ActorNode[];
    total_actors: number;
  }> {
    return this.http.get<{
      conflict: ConflictNode;
      actors: ActorNode[];
      total_actors: number;
    }>(`${this.baseUrl}/conflicts/${conflictName}/actors`);
  }

  /**
   * Obtener red de actores relacionados
   */
  getActorNetwork(
    actorName: string,
    depth: number = 2
  ): Observable<ActorNetwork> {
    const params = new HttpParams().set('depth', depth.toString());
    return this.http.get<ActorNetwork>(
      `${this.baseUrl}/actors/${actorName}/network`,
      {
        params,
      }
    );
  }

  /**
   * Obtener relaciones entre dos actores
   */
  getActorRelationships(
    actor1: string,
    actor2: string
  ): Observable<{
    actor1: string;
    actor2: string;
    relationships: ActorEngagement[];
    total_engagements: number;
  }> {
    return this.http.get<{
      actor1: string;
      actor2: string;
      relationships: ActorEngagement[];
      total_engagements: number;
    }>(`${this.baseUrl}/actors/${actor1}/relationships/${actor2}`);
  }

  /**
   * Obtener top conflictos por impacto
   */
  getTopConflicts(limit: number = 10): Observable<ConflictNode[]> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<ConflictNode[]>(`${this.baseUrl}/conflicts/top`, {
      params,
    });
  }

  /**
   * Obtener actores más letales
   */
  getTopActorsByDeaths(limit: number = 10): Observable<TopActor[]> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<TopActor[]>(`${this.baseUrl}/actors/top/deadliest`, {
      params,
    });
  }

  /**
   * Obtener lista de todos los actores
   */
  getAllActors(limit: number = 100): Observable<string[]> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<string[]>(`${this.baseUrl}/actors`, { params });
  }

  /**
   * Buscar conflictos
   */
  searchConflicts(
    query: string,
    limit: number = 20
  ): Observable<ConflictNode[]> {
    const params = new HttpParams()
      .set('q', query)
      .set('limit', limit.toString());

    return this.http.get<ConflictNode[]>(`${this.baseUrl}/search`, { params });
  }

  /**
   * Obtener estadísticas del grafo
   */
  getGraphStats(): Observable<GraphStats> {
    return this.http.get<GraphStats>(`${this.baseUrl}/stats`);
  }
}
