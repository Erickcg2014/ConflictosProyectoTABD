import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-homepage',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './homepage.component.html',
  styleUrls: ['./homepage.component.css']
})
export class HomepageComponent {
  features = [
    {
      icon: 'map',
      title: 'Mapeo Interactivo',
      description: 'Visualiza eventos de conflictos con coordenadas geográficas precisas y agrupación'
    },
    {
      icon: 'schedule',
      title: 'Análisis Temporal',
      description: 'Rastrea patrones de conflictos a lo largo del tiempo con visualización detallada de línea temporal'
    },
    {
      icon: 'bar_chart',
      title: 'Perspectivas Estadísticas',
      description: 'Análisis completo y datos agregados por región y tipo de conflicto'
    }
  ];
}
