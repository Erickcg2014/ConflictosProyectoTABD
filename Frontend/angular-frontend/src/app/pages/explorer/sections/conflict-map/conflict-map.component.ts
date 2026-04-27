import {
  Component,
  OnInit,
  OnDestroy,
  ViewChild,
  ElementRef,
} from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import * as d3 from 'd3';
import { FormsModule } from '@angular/forms';
import {
  ConflictMapService,
  GraphFilterType,
  FilterItem,
  GraphResponse,
  GraphNode,
  GraphEdge,
  NodeDetails,
} from '../../../../core/services/conflict_map.service';

// ======================================================
// INTERFACES
// ======================================================

interface GraphVisualizationData {
  nodes: any[];
  edges: any[];
  summary?: {
    total_nodes: number;
    total_edges: number;
    total_deaths: number;
  };
}

interface LoadingState {
  initial: boolean;
  filters: boolean;
  graph: boolean;
  details: boolean;
}

interface ErrorState {
  initial: string | null;
  filters: string | null;
  graph: string | null;
  details: string | null;
}

// ======================================================
// COMPONENTE
// ======================================================

@Component({
  selector: 'app-conflict-map',
  templateUrl: './conflict-map.component.html',
  styleUrls: ['./conflict-map.component.css'],
  imports: [CommonModule, FormsModule],
})
export class ConflictMapComponent implements OnInit, OnDestroy {
  @ViewChild('graphContainer', { static: false }) graphContainer!: ElementRef;

  private destroy$ = new Subject<void>();
  private searchSubject$ = new Subject<string>();

  private svg: any;
  private simulation: any;
  private g: any;

  // ===== Estado del filtro =====
  filterType: GraphFilterType = GraphFilterType.COUNTRY;
  GraphFilterType = GraphFilterType;

  availableFilters: FilterItem[] = [];
  filteredFilters: FilterItem[] = [];
  searchTerm: string = '';
  selectedEntity: string | null = null;

  // ===== Estado del grafo =====
  graphData: GraphResponse | null = null;
  visualizationData: GraphVisualizationData | null = null;
  graphDepth: number = 1;

  // ===== Estado de detalles del nodo =====
  selectedNode:
    | (NodeDetails & {
        name?: string;
        region?: string;
        type?: string;
        statistics?: {
          total_conflicts?: number;
          total_deaths?: number;
          total_events?: number;
          total_encounters?: number;
          connections?: number;
          countries_active?: number;
        };
        top_conflicts?: any[];
        connected_entities?: any[];
        actors_involved?: any[];
      })
    | null = null;
  showDetailsPanel: boolean = false;

  // ===== Estados de carga y error =====
  loading: LoadingState = {
    initial: true,
    filters: false,
    graph: false,
    details: false,
  };

  error: ErrorState = {
    initial: null,
    filters: null,
    graph: null,
    details: null,
  };

  // ===== Estado de salud del servicio =====
  serviceHealthy: boolean = false;

  // ===== Constructor =====
  constructor(private conflictMapService: ConflictMapService) {}

  // ======================================================
  // LIFECYCLE HOOKS
  // ======================================================

  ngOnInit(): void {
    console.log('🚀 ConflictMapComponent initialized');

    // Iniciar carga inicial
    this.loading.initial = true;

    this.setupSearchDebounce();

    this.checkServiceHealth();
  }
  ngAfterViewInit(): void {
    console.log('📐 ViewInit - Verificando contenedor del grafo...');

    setTimeout(() => {
      if (this.graphContainer) {
        const element = this.graphContainer.nativeElement;
        const rect = element.getBoundingClientRect();

        console.log('📐 Dimensiones del contenedor:');
        console.log('   Element:', element);
        console.log('   Width:', rect.width, 'px');
        console.log('   Height:', rect.height, 'px');
        console.log('   Top:', rect.top);
        console.log('   Left:', rect.left);
        console.log('   Display:', window.getComputedStyle(element).display);
        console.log(
          '   Visibility:',
          window.getComputedStyle(element).visibility
        );
        console.log('   Opacity:', window.getComputedStyle(element).opacity);

        if (rect.width === 0 || rect.height === 0) {
          console.error('❌ CONTENEDOR TIENE TAMAÑO 0!');
        } else {
          console.log('✅ Contenedor tiene dimensiones válidas');
        }
      } else {
        console.error('❌ graphContainer es undefined!');
      }
    }, 500);
  }

  ngOnDestroy(): void {
    if (this.simulation) {
      this.simulation.stop();
    }
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ======================================================
  // MÉTODOS DE INICIALIZACIÓN
  // ======================================================

  /**
   * Verifica que el servicio de backend esté disponible
   */
  public checkServiceHealth(): void {
    this.conflictMapService
      .healthCheck()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (health) => {
          this.serviceHealthy = health.neo4j_connected && health.data_available;

          if (!this.serviceHealthy) {
            console.warn('⚠️ Service unhealthy:', health.message);
            this.error.initial =
              'Base de datos no disponible. Verificando conexión...';

            // Intentar nuevamente después de un tiempo
            setTimeout(() => {
              this.checkServiceHealth();
            }, 5000);
          } else {
            console.log('✅ Service healthy');
            this.error.initial = null;

            // Solo cargar filtros si el servicio está saludable
            this.loadFilters();
          }

          this.loading.initial = false;
        },
        error: (err) => {
          console.error('❌ Health check failed:', err);
          this.serviceHealthy = false;
          this.error.initial =
            'Error de conexión con el servidor. Por favor, intenta más tarde.';
          this.loading.initial = false;

          // Reintentar después de 5 segundos
          setTimeout(() => {
            this.checkServiceHealth();
          }, 5000);
        },
      });
  }

  /**
   * Configura el debounce para la búsqueda
   */
  private setupSearchDebounce(): void {
    this.searchSubject$
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntil(this.destroy$))
      .subscribe((searchTerm) => {
        this.performSearch(searchTerm);
      });
  }

  // ======================================================
  // MÉTODOS DE FILTROS
  // ======================================================

  /**
   * Verifica si el componente está en estado de carga inicial
   */
  isInitializing(): boolean {
    return this.loading.initial && !this.error.initial;
  }

  /**
   * Verifica si hay un error crítico que impide el funcionamiento
   */
  hasCriticalError(): boolean {
    return !!this.error.initial && !this.loading.initial;
  }

  /**
   * Verifica si el componente está listo para usar
   */
  isReady(): boolean {
    return !this.loading.initial && !this.error.initial;
  }
  /**
   * Carga la lista de filtros disponibles
   */
  loadFilters(): void {
    this.loading.filters = true;
    this.error.filters = null;

    this.conflictMapService
      .getFilters(this.filterType)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.availableFilters = response.items;
          this.filteredFilters = response.items;
          this.loading.filters = false;

          // Marcar carga inicial como completa
          this.loading.initial = false;

          console.log(`✅ Loaded ${response.count} ${this.filterType} filters`);
        },
        error: (err) => {
          console.error('❌ Error loading filters:', err);
          this.error.filters =
            'Error al cargar filtros. Por favor, intenta de nuevo.';
          this.loading.filters = false;
          this.loading.initial = false;
        },
      });
  }

  /**
   * Maneja el cambio de tipo de filtro (país/actor)
   */
  onFilterTypeChange(type: GraphFilterType): void {
    console.log(`🔄 Filter type changed to: ${type}`);

    this.filterType = type;
    this.selectedEntity = null;
    this.searchTerm = '';
    this.graphData = null;
    this.selectedNode = null;
    this.showDetailsPanel = false;

    this.loadFilters();
  }

  /**
   * Maneja el input de búsqueda
   */
  onSearchInput(term: string): void {
    this.searchTerm = term;
    this.searchSubject$.next(term);
  }

  /**
   * Realiza la búsqueda de filtros
   */
  private performSearch(term: string): void {
    if (!term || term.trim().length < 2) {
      this.filteredFilters = this.availableFilters;
      return;
    }

    const lowerTerm = term.toLowerCase();
    this.filteredFilters = this.availableFilters.filter((item) =>
      item.label.toLowerCase().includes(lowerTerm)
    );

    console.log(`🔍 Search "${term}": ${this.filteredFilters.length} results`);
  }

  /**
   * Maneja la selección de una entidad
   */
  onEntitySelect(entity: string): void {
    console.log(`✅ Entity selected: ${entity}`);

    this.selectedEntity = entity;
    this.loadGraph(entity);
  }

  // ======================================================
  // MÉTODOS DEL GRAFO
  // ======================================================

  /**
   * Carga el grafo para la entidad seleccionada
   */
  loadGraph(entity: string): void {
    this.loading.graph = true;
    this.error.graph = null;

    this.conflictMapService
      .getGraphNodes(this.filterType, entity, this.graphDepth)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.graphData = response;
          this.prepareVisualizationData(response);
          this.loading.graph = false;

          console.log('✅ Graph loaded:', {
            nodes: response.summary.total_nodes,
            edges: response.summary.total_edges,
            deaths: response.summary.total_deaths,
          });

          setTimeout(() => this.renderGraph(), 0);
        },
        error: (err) => {
          console.error('❌ Error loading graph:', err);

          if (err.status === 404) {
            this.error.graph = `No se encontró "${entity}". Por favor, verifica el nombre.`;
          } else {
            this.error.graph =
              'Error al cargar el grafo. Por favor, intenta de nuevo.';
          }

          this.loading.graph = false;
        },
      });
  }

  /**
   * Prepara los datos para la visualización
   * Transforma GraphResponse en formato compatible con D3.js/Cytoscape
   */
  private prepareVisualizationData(response: GraphResponse): void {
    // ===== VERIFICACIONES DE SEGURIDAD =====
    if (!response) {
      console.warn(
        '⚠️ prepareVisualizationData: Response is null or undefined'
      );
      this.visualizationData = { nodes: [], edges: [] };
      return;
    }

    if (!response.center_node || !response.nodes || !response.edges) {
      console.warn(
        '⚠️ prepareVisualizationData: Missing required data in response',
        {
          hasCenterNode: !!response.center_node,
          hasNodes: !!response.nodes,
          hasEdges: !!response.edges,
        }
      );
      this.visualizationData = { nodes: [], edges: [] };
      return;
    }

    // ===== PREPARAR DATOS CON VALORES POR DEFECTO =====
    const allNodes = [response.center_node, ...(response.nodes || [])];

    // Calcular máximos para normalización
    const maxDeaths = Math.max(
      1, // Valor mínimo para evitar división por cero
      ...allNodes.map((n) => n.metrics?.total_deaths || 0)
    );

    const maxConnections = Math.max(
      1,
      ...allNodes.map((n) => n.metrics?.connections || 0)
    );

    const maxWeight = Math.max(
      1,
      ...(response.edges || []).map((e) => e?.weight || 0)
    );

    // ===== TRANSFORMAR NODOS CON MANEJO SEGURO =====
    const nodes = allNodes
      .map((node) => {
        if (!node) {
          console.warn(
            '⚠️ prepareVisualizationData: Found null/undefined node'
          );
          return null;
        }

        const metrics = node.metrics || {};
        const nodeId = node.id || 'unknown';
        const nodeLabel = node.label || 'Sin nombre';
        const nodeType = node.type || 'unknown';
        const nodeRegion = node.region || 'Desconocida';

        return {
          id: nodeId,
          label: nodeLabel,
          type: nodeType,
          region: nodeRegion,

          // Métricas con valores por defecto
          deaths: metrics.total_deaths || 0,
          conflicts: metrics.total_conflicts || 0,
          connections: metrics.connections || 0,

          size: this.conflictMapService.getNodeSize(
            metrics.connections || 0,
            maxConnections,
            30, // NÚMERO MAXIMO DE CONEXIONES
            70 // NÚMERO MÁXIMO DE CONEXIONES
          ),
          color: this.conflictMapService.getColorByIntensity(
            metrics.total_deaths || 0,
            maxDeaths
          ),

          // Identificar nodo central
          isCenterNode: nodeId === (response.center_node?.id || ''),
        };
      })
      .filter((node): node is NonNullable<typeof node> => node !== null);

    // ===== TRANSFORMAR ARISTAS CON MANEJO SEGURO =====
    const edges = (response.edges || [])
      .map((edge) => {
        if (!edge) {
          console.warn(
            '⚠️ prepareVisualizationData: Found null/undefined edge'
          );
          return null;
        }

        const edgeMetrics = edge.metrics || {};

        return {
          id: edge.id || `edge-${Math.random().toString(36).substr(2, 9)}`,
          source: edge.source || 'unknown',
          target: edge.target || 'unknown',

          weight: edge.weight || 0,
          eventCount: edgeMetrics.event_count || 0,
          encounterCount: edgeMetrics.encounter_count || 0,
          conflictNames: edgeMetrics.conflict_names || [],
          actorsInvolved: edgeMetrics.actors_involved || [],

          // Propiedades visuales
          width: this.conflictMapService.getEdgeWidth(
            edge.weight || 0,
            maxWeight,
            1,
            8
          ),
        };
      })
      .filter((edge): edge is NonNullable<typeof edge> => edge !== null);

    // ===== ASIGNAR DATOS FINALES =====
    this.visualizationData = {
      nodes,
      edges,
      summary: response.summary
        ? {
            total_nodes: response.summary.total_nodes || 0,
            total_edges: response.summary.total_edges || 0,
            total_deaths: response.summary.total_deaths || 0,
          }
        : {
            total_nodes: nodes.length,
            total_edges: edges.length,
            total_deaths: nodes.reduce(
              (sum, node) => sum + (node.deaths || 0),
              0
            ),
          },
    };

    console.log('📊 Visualization data prepared:', {
      nodes: nodes.length,
      edges: edges.length,
      validNodes: nodes.filter((n) => n.id && n.id !== 'unknown').length,
      validEdges: edges.filter(
        (e) => e.source !== 'unknown' && e.target !== 'unknown'
      ).length,
      maxDeaths,
      maxConnections,
      maxWeight,
    });

    const problematicNodes = nodes.filter((n) => !n.id || n.id === 'unknown');
    const problematicEdges = edges.filter(
      (e) =>
        !e.source ||
        !e.target ||
        e.source === 'unknown' ||
        e.target === 'unknown'
    );

    if (problematicNodes.length > 0) {
      console.warn(
        `⚠️ ${problematicNodes.length} nodos con ID problemático`,
        problematicNodes
      );
    }

    if (problematicEdges.length > 0) {
      console.warn(
        `⚠️ ${problematicEdges.length} aristas con source/target problemático`,
        problematicEdges
      );
    }
  }

  /**
   * Renderiza el grafo con D3.js
   */

  private renderGraph(): void {
    if (!this.visualizationData || !this.graphContainer) {
      console.warn('⚠️ Cannot render graph: missing data or container');
      return;
    }

    console.log('🎨 Rendering graph...');
    console.log('Nodes:', this.visualizationData.nodes);
    console.log('Edges:', this.visualizationData.edges);

    const element = this.graphContainer.nativeElement;
    const rect = element.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    console.log('📐 Container dimensions:', width, 'x', height);

    if (width === 0 || height === 0) {
      console.error('❌ Container has zero dimensions, retrying...');
      setTimeout(() => this.renderGraph(), 100);
      return;
    }

    try {
      d3.select(element).selectAll('*').remove();

      // Crear SVG
      this.svg = d3
        .select(element)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height])
        .style('background-color', '#f8f9fa');

      this.g = this.svg.append('g');

      // Zoom behavior
      const zoom = d3
        .zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.1, 4])
        .on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
          this.g.attr('transform', event.transform);
        });

      this.svg.call(zoom);

      // Preparar datos
      const nodes = this.visualizationData.nodes.map((d) => ({ ...d }));
      const links = this.visualizationData.edges.map((d) => ({
        source: d.source,
        target: d.target,
        weight: d.weight,
        width: d.width,
      }));

      console.log('Data prepared:', {
        nodes: nodes.length,
        links: links.length,
      });

      // Crear simulación de fuerzas
      this.simulation = d3
        .forceSimulation(nodes)
        .force(
          'link',
          d3
            .forceLink(links)
            .id((d: any) => d.id)
            .distance(120) // ✅ Más espacio entre nodos
        )
        .force('charge', d3.forceManyBody().strength(-600)) // Más repulsión
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force(
          'collision',
          d3.forceCollide().radius((d) => (d as any).size + 15) // Más espacio
        );

      this.svg
        .append('defs')
        .selectAll('marker')
        .data(['arrow'])
        .join('marker')
        .attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('fill', '#999')
        .attr('d', 'M0,-5L10,0L0,5');

      const link = this.g
        .append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.4)
        .attr('stroke-width', (d: any) => Math.max(d.width * 0.5, 1))
        .attr('marker-end', 'url(#arrow)');

      const node = this.g
        .append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .call(this.drag(this.simulation) as any);

      node
        .append('circle')
        .attr('r', (d: any) => d.size || 10)
        .attr('fill', (d: any) => d.color || '#69b3a2')
        .attr('stroke', (d: any) => {
          if (d.isCenterNode) return '#FFD700';
          return '#ffffff';
        })
        .attr('stroke-width', (d: any) => (d.isCenterNode ? 5 : 2.5))
        .style('cursor', 'pointer')
        .style('filter', (d: any) => {
          return d.isCenterNode
            ? 'drop-shadow(0 0 12px rgba(255, 215, 0, 0.8))'
            : 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))';
        });

      node
        .append('text')
        .text((d: any) => d.label)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('font-size', (d: any) => {
          const size = d.size || 10;
          if (size > 35) return 13;
          if (size > 25) return 11;
          return 10;
        })
        .attr('font-weight', (d: any) => (d.isCenterNode ? 'bold' : 'normal'))
        .attr('fill', (d: any) => {
          const size = d.size || 10;
          const color = d.color || '#69b3a2';

          if (size > 30 || ['#8B0000', '#DC143C', '#FF6347'].includes(color)) {
            return '#ffffff';
          }
          return '#333333';
        })
        .style('pointer-events', 'none')
        .style('user-select', 'none')
        .each(function (this: SVGTextElement, d: any) {
          const size = d.size || 10;
          const maxLength = Math.floor(size / 3.5);
          const text = d3.select(this);
          let label = d.label;

          if (label.length > maxLength) {
            label = label.substring(0, maxLength - 2) + '..';
          }

          text.text(label);
        });

      const component = this;

      node.on('click', function (this: SVGGElement, event: MouseEvent, d: any) {
        event.stopPropagation();
        console.log('🖱️ Node clicked:', d.id);
        component.onNodeClick(d.id);
      });

      node.on(
        'mouseover',
        function (this: SVGGElement, _event: MouseEvent, d: any) {
          d3.select(this)
            .select('circle')
            .transition()
            .duration(200)
            .attr('r', (d.size || 10) * 1.2)
            .style('filter', 'drop-shadow(0 0 8px rgba(0,0,0,0.4))');
        }
      );

      node.on(
        'mouseout',
        function (this: SVGGElement, _event: MouseEvent, d: any) {
          d3.select(this)
            .select('circle')
            .transition()
            .duration(200)
            .attr('r', d.size || 10)
            .style(
              'filter',
              d.isCenterNode
                ? 'drop-shadow(0 0 12px rgba(255, 215, 0, 0.8))'
                : 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))'
            );
        }
      );

      const tooltip = d3
        .select(element)
        .append('div')
        .attr('class', 'graph-tooltip')
        .style('position', 'absolute')
        .style('visibility', 'hidden')
        .style(
          'background',
          'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        )
        .style('color', 'white')
        .style('padding', '12px 16px')
        .style('border-radius', '8px')
        .style('font-size', '13px')
        .style('font-family', 'system-ui, -apple-system, sans-serif')
        .style('box-shadow', '0 4px 12px rgba(0,0,0,0.3)')
        .style('pointer-events', 'none')
        .style('z-index', '1000')
        .style('max-width', '250px')
        .style('line-height', '1.6');

      node.on(
        'mousemove',
        function (this: SVGGElement, event: MouseEvent, d: any) {
          tooltip
            .style('visibility', 'visible')
            .html(
              `
          <div style="font-weight: bold; font-size: 15px; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 6px;">
            ${d.label}
          </div>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <div><span style="opacity: 0.8;">🌍 Región:</span> <strong>${
              d.region
            }</strong></div>
            <div><span style="opacity: 0.8;">💀 Muertes:</span> <strong>${d.deaths.toLocaleString()}</strong></div>
            <div><span style="opacity: 0.8;">🔗 Conexiones:</span> <strong>${
              d.connections
            }</strong></div>
            <div><span style="opacity: 0.8;">⚔️ Conflictos:</span> <strong>${
              d.conflicts
            }</strong></div>
          </div>
          <div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.3); font-size: 11px; opacity: 0.8;">
            Click para ver detalles completos
          </div>
        `
            )
            .style('left', event.pageX + 15 + 'px')
            .style('top', event.pageY - 10 + 'px');
        }
      );

      node.on('mouseout', () => {
        tooltip.style('visibility', 'hidden');
      });

      this.simulation.on('tick', () => {
        link
          .attr('x1', (d: any) => d.source.x)
          .attr('y1', (d: any) => d.source.y)
          .attr('x2', (d: any) => d.target.x)
          .attr('y2', (d: any) => d.target.y);

        node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
      });

      console.log('✅ Graph rendered successfully with D3.js');

      // Zoom inicial para centrar el grafo
      setTimeout(() => {
        const bounds = this.g.node().getBBox();
        const fullWidth = bounds.width;
        const fullHeight = bounds.height;
        const midX = bounds.x + fullWidth / 2;
        const midY = bounds.y + fullHeight / 2;

        const scale = 0.75 / Math.max(fullWidth / width, fullHeight / height);
        const translate = [width / 2 - scale * midX, height / 2 - scale * midY];

        this.svg
          .transition()
          .duration(750)
          .call(
            zoom.transform,
            d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
          );
      }, 100);
    } catch (error) {
      console.error('❌ Error rendering graph:', error);
    }
  }
  /**
   * Función de drag para los nodos
   */
  private drag(simulation: any) {
    function dragstarted(event: d3.D3DragEvent<any, any, any>, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: d3.D3DragEvent<any, any, any>, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<any, any, any>, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return d3
      .drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  }

  /**
   * Maneja el click en un nodo del grafo
   */
  onNodeClick(nodeId: string): void {
    console.log(`🖱️ Node clicked: ${nodeId}`);

    this.loadNodeDetails(nodeId);
  }

  /**
   * Cambia la profundidad del grafo
   */
  onDepthChange(depth: number): void {
    if (depth === this.graphDepth) return;

    console.log(`🔄 Depth changed to: ${depth}`);

    this.graphDepth = depth;

    if (this.selectedEntity) {
      this.loadGraph(this.selectedEntity);
    }
  }

  // ======================================================
  // MÉTODOS DE DETALLES DE NODO
  // ======================================================

  /**
   * Carga los detalles de un nodo específico
   */
  loadNodeDetails(nodeId: string): void {
    this.loading.details = true;
    this.error.details = null;
    this.showDetailsPanel = true;

    this.conflictMapService
      .getNodeDetails(this.filterType, nodeId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (details) => {
          this.selectedNode = {
            ...details,
            statistics: details.statistics || {},
            top_conflicts: details.top_conflicts || [],
            connected_entities: details.connected_entities || [],
            actors_involved: details.actors_involved || [],
          };
          this.loading.details = false;
          console.log('✅ Node details loaded:', details.name);
        },
        error: (err) => {
          console.error('❌ Error loading node details:', err);
          this.error.details = 'Error al cargar detalles del nodo.';
          this.loading.details = false;
          this.selectedNode = null;
        },
      });
  }

  /**
   * Cierra el panel de detalles
   */
  closeDetailsPanel(): void {
    this.showDetailsPanel = false;
    this.selectedNode = null;
  }

  /**
   * Formatea números con separadores de miles
   */
  formatNumber(value: number | undefined | null): string {
    if (value === undefined || value === null) {
      return '0';
    }
    return this.conflictMapService.formatNumber(value);
  }

  /**
   * Resetea el grafo y vuelve al estado inicial
   */
  resetGraph(): void {
    console.log('🔄 Resetting graph');

    this.selectedEntity = null;
    this.graphData = null;
    this.visualizationData = null;
    this.selectedNode = null;
    this.showDetailsPanel = false;
    this.searchTerm = '';
    this.graphDepth = 1;

    this.loadFilters();
  }

  downloadGraphAsImage(): void {
    console.log('📸 Downloading graph as image...');
    alert('Función de descarga en desarrollo');
  }

  /**
   * Obtiene el título del tipo de filtro
   */
  getFilterTypeLabel(): string {
    return this.filterType === GraphFilterType.COUNTRY ? 'País' : 'Actor';
  }

  /**
   * Verifica si hay datos de grafo cargados
   */

  hasGraphData(): boolean {
    console.log('🔍 hasGraphData() called');
    console.log('   graphData:', this.graphData);
    console.log('   nodes:', this.graphData?.nodes?.length);
    console.log('   edges:', this.graphData?.edges?.length);

    const hasData = Boolean(
      this.graphData && this.graphData.nodes && this.graphData.nodes.length > 0
    );

    console.log('   Result:', hasData);
    return hasData;
  }

  /**
   * Obtiene mensaje de estado del grafo
   */
  getGraphStatusMessage(): string {
    if (this.loading.graph) {
      return 'Cargando grafo...';
    }

    if (this.error.graph) {
      return this.error.graph;
    }

    if (!this.selectedEntity) {
      return `Selecciona un ${this.getFilterTypeLabel().toLowerCase()} para visualizar el grafo`;
    }

    if (this.hasGraphData() && this.graphData?.summary) {
      const summary = this.graphData.summary;
      return `Mostrando ${summary.total_nodes} nodos y ${summary.total_edges} conexiones`;
    }

    return 'Listo para cargar grafo';
  }
  /**
   * Obtiene color basado en el número de muertes
   */
  private getNodeColorByDeaths(deaths: number, maxDeaths: number): string {
    const ratio = deaths / maxDeaths;

    if (ratio > 0.7) return '#8B0000';
    if (ratio > 0.5) return '#DC143C';
    if (ratio > 0.3) return '#FF6347';
    if (ratio > 0.15) return '#FF8C00';
    if (ratio > 0.05) return '#FFA500';
    if (ratio > 0.01) return '#FFD700';
    return '#87CEEB';
  }
}
