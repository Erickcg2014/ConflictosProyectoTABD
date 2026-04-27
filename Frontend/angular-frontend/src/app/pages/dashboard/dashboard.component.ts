import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
  title = 'Dashboard de Conflictos';

  // Estadísticas de ejemplo
  stats = [
    {
      title: 'Total de Conflictos',
      value: '1,234',
      icon: 'military_tech',
      change: '+12%',
      changeType: 'positive'
    },
    {
      title: 'Países Afectados',
      value: '45',
      icon: 'public',
      change: '+3',
      changeType: 'positive'
    },
    {
      title: 'Eventos este Mes',
      value: '87',
      icon: 'event',
      change: '-8%',
      changeType: 'negative'
    },
    {
      title: 'Víctimas Registradas',
      value: '15,678',
      icon: 'group',
      change: '+5%',
      changeType: 'positive'
    }
  ];

  // Enlaces rápidos
  quickLinks = [
    {
      title: 'Explorar Datos',
      description: 'Navega por el conjunto completo de datos de conflictos',
      icon: 'explore',
      route: '/explorer'
    },
    {
      title: 'Análisis Estadístico',
      description: 'Visualiza tendencias y patrones estadísticos',
      icon: 'bar_chart',
      route: '/statistics'
    },
    {
      title: 'Mapas Geoespaciales',
      description: 'Visualiza conflictos en mapas interactivos',
      icon: 'map',
      route: '/geospatial'
    },
    {
      title: 'Redes de Actores',
      description: 'Analiza relaciones entre actores en conflictos',
      icon: 'hub',
      route: '/networks'
    }
  ];
}
