// pages/explorer/sections/mapa-interactivo/mapa-interactivo.component.ts
import {
  Component,
  OnInit,
  AfterViewInit,
  OnDestroy,
  Inject,
  PLATFORM_ID,
} from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { CommonModule } from '@angular/common';
import {
  MongodbService,
  WarLocation,
  ClusterData,
} from '../../../../core/services/mongodb.service';
import { BigqueryService } from '../../../../core/services/bigquery.service';

@Component({
  selector: 'app-mapa-interactivo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mapa-interactivo.component.html',
  styleUrls: ['./mapa-interactivo.component.css'],
})
export class MapaInteractivoComponent
  implements OnInit, AfterViewInit, OnDestroy
{
  private map: any = null;
  private markerClusterGroup: any = null;
  private currentZoom = 2;
  private isLoading = false;
  private isBrowser = false;
  private leafletLoaded = false;

  private REGION_BOUNDS: Record<
    string,
    {
      center: [number, number];
      zoom: number;
      bounds: {
        min_lon: number;
        min_lat: number;
        max_lon: number;
        max_lat: number;
      };
    }
  > = {
    // Incluye Norte, Centro y Suramérica
    america: {
      center: [15, -80], // Cerca del Caribe
      zoom: 3,
      bounds: {
        min_lon: -170, // Alaska / Pacífico
        min_lat: -60, // Sur de Chile/Argentina
        max_lon: -30, // Atlántico, antes de África
        max_lat: 75, // Canadá / Groenlandia sur
      },
    },

    europa: {
      center: [54, 15], // Centro-Europa
      zoom: 4,
      bounds: {
        min_lon: -25, // Portugal / Atlántico
        min_lat: 34, // Mediterráneo (España, Italia, Grecia)
        max_lon: 45, // Frontera oeste con Asia
        max_lat: 72, // Escandinavia
      },
    },

    africa: {
      center: [2, 20], // Centro aproximado del continente
      zoom: 4,
      bounds: {
        min_lon: -20, // Costa oeste
        min_lat: -35, // Sur (Sudáfrica)
        max_lon: 55, // Cuerno de África / Golfo de Adén
        max_lat: 38, // Límite norte (Mediterráneo)
      },
    },

    asia: {
      center: [34, 90], // Centro aproximado de Asia
      zoom: 3,
      bounds: {
        min_lon: 25, // Empieza donde termina Europa / ME
        min_lat: -10, // Incluye parte del sudeste asiático
        max_lon: 150, // Hasta Japón / Pacífico
        max_lat: 75, // Siberia
      },
    },

    'medio-oriente': {
      center: [28, 45], // Zona Irak / Siria
      zoom: 5,
      bounds: {
        min_lon: 30, // Israel / Jordania
        min_lat: 12, // Sur de Arabia Saudita
        max_lon: 65, // Irán / Golfo Pérsico
        max_lat: 40, // Turquía / norte de Irak
      },
    },

    oceania: {
      center: [-20, 135], // Centro aproximado de Australia
      zoom: 4,
      bounds: {
        min_lon: 105, // Oeste de Australia
        min_lat: -45, // Sur de Nueva Zelanda
        max_lon: 180, // Pacífico oeste
        max_lat: 5, // Norte de Papúa / islas vecinas
      },
    },
  };

  constructor(
    private mongodbService: MongodbService,
    private bigqueryService: BigqueryService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  ngOnInit() {
    console.log('🗺️ Mapa Interactivo: Componente inicializado');

    if (this.isBrowser) {
      this.loadLeafletScripts();
    }
  }

  ngAfterViewInit() {
    if (this.isBrowser) {
      setTimeout(() => {
        this.initMap();
      }, 100);
    }
  }

  // ======================================================
  // CARGA DE SCRIPTS LEAFLET
  // ======================================================

  private loadLeafletScripts(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (
        (window as any).L &&
        typeof (window as any).L.markerClusterGroup === 'function'
      ) {
        console.log('Leaflet ya estaba cargado');
        this.leafletLoaded = true;
        resolve();
        return;
      }

      // Cargar Leaflet primero
      const leafletScript = document.createElement('script');
      leafletScript.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      leafletScript.integrity =
        'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
      leafletScript.crossOrigin = '';

      leafletScript.onload = () => {
        console.log('Leaflet.js cargado');

        const markerClusterScript = document.createElement('script');
        markerClusterScript.src =
          'https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js';

        markerClusterScript.onload = () => {
          console.log('✅ MarkerCluster.js cargado');
          this.leafletLoaded = true;
          resolve();
        };

        markerClusterScript.onerror = (error) => {
          console.error('❌ Error cargando MarkerCluster:', error);
          reject(error);
        };

        document.head.appendChild(markerClusterScript);
      };

      leafletScript.onerror = (error) => {
        console.error('❌ Error cargando Leaflet:', error);
        reject(error);
      };

      document.head.appendChild(leafletScript);
    });
  }

  private waitForLeaflet(): Promise<void> {
    return new Promise((resolve, reject) => {
      const maxAttempts = 100;
      let attempts = 0;

      const checkLeaflet = () => {
        const L = (window as any).L;

        if (L && typeof L.markerClusterGroup === 'function') {
          console.log('Leaflet verificado y listo');
          resolve();
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(checkLeaflet, 100);
        } else {
          reject(new Error('Leaflet no se cargó a tiempo'));
        }
      };

      checkLeaflet();
    });
  }

  // ======================================================
  // INICIALIZACIÓN DEL MAPA
  // ======================================================

  private initMap(): void {
    if (!this.isBrowser) {
      console.error('❌ No está en browser');
      return;
    }

    this.waitForLeaflet()
      .then(() => {
        const L = (window as any).L;

        if (!L || typeof L.markerClusterGroup !== 'function') {
          console.error('❌ Leaflet o MarkerCluster no están disponibles');
          return;
        }

        console.log('Leaflet y MarkerCluster listos para usar');

        try {
          delete (L.Icon.Default.prototype as any)._getIconUrl;
          L.Icon.Default.mergeOptions({
            iconRetinaUrl:
              'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
            iconUrl:
              'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
            shadowUrl:
              'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
          });

          this.map = L.map('map', {
            center: [20, 0],
            zoom: 2,
            minZoom: 2,
            maxZoom: 18,
            zoomControl: true,
          });

          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '© OpenStreetMap contributors',
          }).addTo(this.map);

          this.markerClusterGroup = L.markerClusterGroup({
            chunkedLoading: true,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            zoomToBoundsOnClick: true,
            maxClusterRadius: 80,
            iconCreateFunction: (cluster: any) => {
              const count = cluster.getChildCount();
              let size = 'small';

              if (count > 100) size = 'large';
              else if (count > 10) size = 'medium';

              return L.divIcon({
                html: `<div><span>${count}</span></div>`,
                className: `marker-cluster marker-cluster-${size}`,
                iconSize: L.point(40, 40),
              });
            },
          });

          this.map.addLayer(this.markerClusterGroup);
          this.map.on('zoomend', () => this.onMapChange());
          this.map.on('moveend', () => this.onMapChange());

          this.map.whenReady(() => {
            console.log('🗺️ Mapa completamente listo');
            setTimeout(() => {
              this.loadMapData();
            }, 200);
          });

          console.log('✅ Mapa inicializado correctamente');
        } catch (error) {
          console.error('❌ Error al inicializar el mapa:', error);
        }
      })
      .catch((error) => {
        console.error('❌ Error esperando a Leaflet:', error);
      });
  }

  // ======================================================
  // MÉTODOS PÚBLICOS
  // ======================================================

  public refreshMap(): void {
    if (this.map) {
      setTimeout(() => {
        this.map.invalidateSize();
      }, 300);
    }
  }

  // ======================================================
  // EVENTOS DEL MAPA
  // ======================================================

  private onMapChange(): void {
    if (!this.map) return;

    const newZoom = this.map.getZoom();

    if (Math.abs(newZoom - this.currentZoom) >= 1) {
      this.currentZoom = newZoom;
      this.loadMapData();
    }
  }

  // ======================================================
  // CARGA DE DATOS
  // ======================================================

  private loadMapData(): void {
    if (!this.map || this.isLoading) return;

    this.isLoading = true;
    this.showLoadingOverlay(true);

    const zoom = this.map.getZoom();
    const bounds = this.map.getBounds();
    const validatedBounds = this.validateBounds(bounds);

    console.log('📍 Cargando datos - Zoom:', zoom, 'Bounds:', validatedBounds);

    if (zoom <= 5) {
      this.loadClusteredData(zoom, validatedBounds);
    } else {
      this.loadBoundedData(validatedBounds);
    }
  }

  private validateBounds(bounds: any): {
    min_lon: number;
    min_lat: number;
    max_lon: number;
    max_lat: number;
  } {
    let minLon = bounds.getWest();
    let maxLon = bounds.getEast();
    let minLat = bounds.getSouth();
    let maxLat = bounds.getNorth();

    // Validar latitudes (deben estar entre -90 y 90)
    minLat = Math.max(-90, Math.min(90, minLat));
    maxLat = Math.max(-90, Math.min(90, maxLat));

    // Validar longitudes (deben estar entre -180 y 180)
    minLon = Math.max(-180, Math.min(180, minLon));
    maxLon = Math.max(-180, Math.min(180, maxLon));

    // Asegurar que min < max
    if (minLat >= maxLat) {
      [minLat, maxLat] = [maxLat, minLat];
    }
    if (minLon >= maxLon) {
      [minLon, maxLon] = [maxLon, minLon];
    }

    return {
      min_lon: Number(minLon.toFixed(6)),
      min_lat: Number(minLat.toFixed(6)),
      max_lon: Number(maxLon.toFixed(6)),
      max_lat: Number(maxLat.toFixed(6)),
    };
  }
  public filterByRegion(event: Event): void {
    if (!this.map) {
      console.error('❌ Mapa no inicializado todavía');
      return;
    }

    const target = event.target as HTMLSelectElement | null;

    if (!target) {
      console.error('❌ EventTarget inválido');
      return;
    }

    const region = target.value;

    if (!region) {
      console.warn('⚠️ Región vacía, no se aplica filtro');
      return;
    }

    const config = this.REGION_BOUNDS[region];

    if (!config) {
      console.error('❌ Región no válida:', region);
      return;
    }

    const L = (window as any).L;
    if (!L) {
      console.error('❌ Leaflet no está disponible');
      return;
    }

    console.log('🌍 Filtrando por región:', region, config);

    const leafletBounds = L.latLngBounds(
      [config.bounds.min_lat, config.bounds.min_lon],
      [config.bounds.max_lat, config.bounds.max_lon]
    );

    this.map.fitBounds(leafletBounds);

    this.currentZoom = this.map.getZoom();

    this.loadMapData();
  }

  private loadClusteredData(zoom: number, bounds: any): void {
    console.log('🔍 Cargando clusters con zoom:', zoom, 'bounds:', bounds);

    this.mongodbService.getMapClusters(zoom, bounds).subscribe({
      next: (clusters) => {
        console.log('✅ Clusters recibidos:', clusters.length);

        const filteredClusters = clusters.filter(
          (cluster) => cluster.count > 1
        );

        if (filteredClusters.length > 0) {
          this.renderClusters(filteredClusters);
        } else {
          console.log(
            '⚠️ No hay clusters suficientes, cargando marcadores individuales'
          );
          this.loadBoundedData(bounds);
        }

        this.isLoading = false;
        this.showLoadingOverlay(false);
      },
      error: (error) => {
        console.error('❌ Error al cargar clusters:', error);

        if (error.status === 422) {
          console.log(
            '⚠️ Error 422, intentando con marcadores individuales...'
          );
          this.loadBoundedData(bounds);
        } else {
          this.isLoading = false;
          this.showLoadingOverlay(false);
        }
      },
    });
  }

  private loadBoundedData(bounds: any): void {
    console.log('📍 Cargando marcadores individuales con bounds:', bounds);

    this.mongodbService
      .getLocationsInBounds(
        bounds.min_lon,
        bounds.min_lat,
        bounds.max_lon,
        bounds.max_lat,
        500
      )
      .subscribe({
        next: (locations) => {
          console.log('✅ Ubicaciones recibidas:', locations.length);
          this.renderMarkers(locations);
          this.isLoading = false;
          this.showLoadingOverlay(false);
        },
        error: (error) => {
          console.error('❌ Error al cargar ubicaciones:', error);
          this.isLoading = false;
          this.showLoadingOverlay(false);
        },
      });
  }

  // ======================================================
  // RENDERIZADO
  // ======================================================

  private renderClusters(clusters: ClusterData[]): void {
    if (!this.markerClusterGroup) return;

    const L = (window as any).L;
    this.markerClusterGroup.clearLayers();

    clusters.forEach((cluster) => {
      const marker = L.marker([cluster.latitude, cluster.longitude], {
        icon: L.divIcon({
          html: `<div class="custom-cluster"><span>${cluster.count}</span></div>`,
          className: 'custom-cluster-icon',
          iconSize: L.point(40, 40),
        }),
      });

      const popupContent = `
        <div class="cluster-popup">
          <h3>${cluster.count} eventos</h3>
          <p><strong>Países:</strong> ${cluster.countries.join(', ')}</p>
          <p><strong>Conflictos:</strong> ${cluster.conflicts
            .slice(0, 3)
            .join(', ')}${cluster.conflicts.length > 3 ? '...' : ''}</p>
        </div>
      `;

      marker.bindPopup(popupContent);
      this.markerClusterGroup!.addLayer(marker);
    });
  }

  private renderMarkers(locations: WarLocation[]): void {
    if (!this.markerClusterGroup) return;

    const L = (window as any).L;
    this.markerClusterGroup.clearLayers();

    locations.forEach((location) => {
      const [lon, lat] = location.location.coordinates;
      const marker = L.marker([lat, lon]);

      marker.on('click', () => {
        this.showEventDetails(location.event_id);
      });

      const popupContent = `
        <div class="event-popup">
          <h3>${location.conflict_name}</h3>
          <p><strong>País:</strong> ${location.country}</p>
          <p><strong>Región:</strong> ${location.region}</p>
        </div>
      `;

      marker.bindPopup(popupContent);
      this.markerClusterGroup!.addLayer(marker);
    });
  }

  private showEventDetails(eventId: string): void {
    this.bigqueryService.getConflictById(eventId).subscribe({
      next: (conflict) => {
        console.log('📄 Detalles del evento:', conflict);
      },
      error: (error) => {
        console.error('❌ Error al cargar detalles:', error);
      },
    });
  }

  private showLoadingOverlay(show: boolean): void {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.style.display = show ? 'flex' : 'none';
    }
  }

  // ======================================================
  // DESTRUCCIÓN
  // ======================================================

  ngOnDestroy() {
    if (this.map) {
      console.log('🗑️ Destruyendo mapa...');
      this.map.remove();
      this.map = null;
      this.markerClusterGroup = null;
    }
  }
  public centerMap(): void {
    if (this.map) {
      this.map.setView([20, 0], 2);
      console.log('🗺️ Mapa centrado');
    }
  }

  public toggleFilters(): void {
    console.log('🔍 Filtros activados (pendiente implementación)');
  }

  public toggleLayers(): void {
    console.log('🗂️ Capas activadas (pendiente implementación)');
  }
}
