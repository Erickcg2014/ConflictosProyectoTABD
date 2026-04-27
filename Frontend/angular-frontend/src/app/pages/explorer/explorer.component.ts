import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { ConflictMapComponent } from './sections/conflict-map/conflict-map.component';
import { StatisticsComponent } from './sections/statistics/statistics.component';
import { MapaInteractivoComponent } from './sections/mapa-interactivo/mapa-interactivo.component';

@Component({
  selector: 'app-explorer',
  standalone: true,
  imports: [
    CommonModule,
    NavbarComponent,
    SidebarComponent,
    StatisticsComponent,
    ConflictMapComponent,
    MapaInteractivoComponent,
  ],
  templateUrl: './explorer.component.html',
  styleUrls: ['./explorer.component.css'],
})
export class ExplorerComponent implements OnInit {
  isSidebarOpen = true;
  selectedSection = 'map';

  @ViewChild(MapaInteractivoComponent) mapaComponent?: MapaInteractivoComponent;

  ngOnInit() {
    console.log('Explorer component initialized');
  }

  onSectionSelected(sectionId: string) {
    this.selectedSection = sectionId;
    console.log('Sección seleccionada:', sectionId);

    if (sectionId === 'map' && this.mapaComponent) {
      setTimeout(() => {
        this.mapaComponent?.refreshMap();
      }, 300);
    }
  }

  onToggleSidebar() {
    this.isSidebarOpen = !this.isSidebarOpen;

    if (this.selectedSection === 'map' && this.mapaComponent) {
      setTimeout(() => {
        this.mapaComponent?.refreshMap();
      }, 300);
    }
  }

  getSectionLabel(sectionId: string): string {
    const labels: { [key: string]: string } = {
      statistics: 'Estadísticas Generales',
      map: 'Mapa Interactivo',
      'conflict-map': 'Redes de Actores',
      dataflow: 'Flujo de Datos (DataFlow)',
    };
    return labels[sectionId] || 'Desconocido';
  }

  getSectionIcon(sectionId: string): string {
    const icons: { [key: string]: string } = {
      statistics: 'bar_chart',
      map: 'map',
      'conflict-map': 'hub',
      dataflow: 'account_tree',
    };
    return icons[sectionId] || 'dashboard';
  }
}
