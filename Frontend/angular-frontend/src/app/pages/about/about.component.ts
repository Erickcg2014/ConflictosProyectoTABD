import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule, RouterLink, NavbarComponent],
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.css'],
})
export class AboutComponent {
  databases = [
    {
      name: 'BigQuery',
      icon: 'storage',
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      description:
        'Almacenamiento y análisis estadístico de eventos históricos',
      features: [
        'Consultas SQL de alto rendimiento',
        'Análisis de bastantes registros históricos',
        'Agregaciones y estadísticas en tiempo real',
        'Visualización de tendencias temporales',
      ],
    },
    {
      name: 'Neo4j',
      icon: 'hub',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      description: 'Modelado de relaciones entre actores y redes de conflictos',
      features: [
        'Grafos de relaciones entre actores',
        'Análisis de redes complejas',
        'Detección de patrones y comunidades',
        'Visualización de conexiones',
      ],
    },
    {
      name: 'MongoDB',
      icon: 'location_on',
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-500/10',
      description: 'Gestión de datos geoespaciales y ubicaciones de eventos',
      features: [
        'Consultas geoespaciales eficientes',
        'Almacenamiento de coordenadas',
        'Índices geográficos optimizados',
        'Integración con mapas interactivos',
      ],
    },
  ];

  team = [
    {
      name: 'Erick Santiago Camargo García',
      role: 'Ingeniero de Sistemas',
      icon: 'person',
      color: 'text-primary',
    },
    {
      name: 'Carlos Enrique Caicedo Guerrero',
      role: 'Ingeniero de Sistemas',
      icon: 'person',
      color: 'text-primary',
    },
  ];

  technologies = [
    { name: 'Angular 17+', icon: 'code', category: 'Frontend' },
    { name: 'Python/FastAPI', icon: 'api', category: 'Backend' },
    { name: 'Leaflet', icon: 'map', category: 'Mapas' },
    { name: 'Tailwind CSS', icon: 'palette', category: 'Estilos' },
    { name: 'Apache Airflow', icon: 'schedule', category: 'ETL' },
    { name: 'Docker/Kubernetes', icon: 'cloud', category: 'Infraestructura' },
  ];
}
