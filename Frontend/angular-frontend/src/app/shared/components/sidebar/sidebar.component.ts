import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  active: boolean;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css'],
})
export class SidebarComponent {
  @Input() isOpen = true;
  @Output() toggle = new EventEmitter<void>();
  @Output() sectionSelected = new EventEmitter<string>();

  menuItems: MenuItem[] = [
    {
      id: 'statistics',
      label: 'Estadísticas',
      icon: 'bar_chart',
      active: false,
    },
    {
      id: 'map',
      label: 'Mapa Interactivo',
      icon: 'map',
      active: true,
    },

    {
      id: 'conflict-map',
      label: 'Redes de Actores',
      icon: 'hub',
      active: false,
    },
  ];

  onToggle() {
    this.toggle.emit();
  }

  onSelectItem(itemId: string) {
    this.menuItems.forEach((item) => {
      item.active = item.id === itemId;
    });

    this.sectionSelected.emit(itemId);
  }
}
