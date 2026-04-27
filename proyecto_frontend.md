# Estructura Frontend Angular

## 🎨 ESTRUCTURA - Angular 20+

```
frontend/
│
├── src/
│   ├── app/
│   │   ├── app.component.ts
│   │   ├── app.component.html
│   │   ├── app.component.css
│   │   ├── app.routes.ts
│   │   ├── app.config.ts
│   │   │
│   │   ├── core/
|   |   │   └── services/                      # 🔵 Servicios HTTP
|   │   │        ├── bigquery.service.ts        # BigQuery API
│   │   │        ├── conflict_map.service.ts    # Servicio para redes de actores
│   │   │        ├── dataflow.service.ts        # Servicio para dataflow
│   │   │        ├── neo4j.service.ts           # Neo4j API
│   │   │        ├── mongodb.service.ts         # MongoDB API
│   │   │        └── statistics.service.ts      # Servicio para statistics
│   │   │
│   │   │
│   │   ├── pages/                         # 🟡 Páginas (4 secciones del sidebar)
│   │   │   ├── about/
│   │   │   │     ├── about.component.css
│   │   │   │     ├── about.component.ts
│   │   │   │     └── about.component.html
|   │   │   │
│   │   │   ├── dashboard/
│   │   │   |       ├── homepage/
│   │   │   │       |     ├── homepage.component.ts
│   │   │   │       |     ├── homepage.component.html
│   │   │   │       |     └── homepage.component.css
│   │   │   │       |
│   │   │   |       ├── dashboard.component.css
│   │   │   |       ├── dashboard.component.html
│   │   │   |       └── dashboard.component.ts
│   │   │   └── explorer/
│   │   │       ├── sections/
│   │   │       |     ├── conflict-map/ # Todo lo relacionado con mapas de actores
│   │   │       |     |      ├── conflict-map.component.css
│   │   │       |     |      ├── conflict-map.component.html
│   │   │       |     |      └── conflict-map.component.ts
│   │   │       |     |
│   │   │       |     ├── dataflow/  # Todo lo relacionado con los componentes de dataflow
│   │   │       |     |      ├── dataflow.component.css
│   │   │       |     |      ├── dataflow.component.html
│   │   │       |     |      └── dataflow.component.ts # Sección data flow
│   │   │       |     |
│   │   │       |     ├── mapa-interactivo/   # todavía no tiene, el mapa está en explorer.component.ts, falta pasarlo aquí
│   │   │       |     |
│   │   │       |     └── statistics/ # Todo lo relacionados con estadísticas
│   │   │       |            ├── components/ # Componentes con diferentes contenidos para la sección de estadísticas
│   │   │       |            |       ├── conflicts-table/ # Tabla que lista los conflictos
│   │   │       |            |       |        ├── conflicts-table.component.css
│   │   │       |            |       |        ├── conflicts-table.component.ts
│   │   │       |            |       |        └── conflicts-table.component.html
│   │   │       |            |       ├── stats-card/ # Cards que muestran unas estadísticas generales de los conflictos
│   │   │       |            |       |        ├── stats-card.component.ts
│   │   │       |            |       |        ├── stats-card.component.html
│   │   │       |            |       |        └── stats-card.component.css
│   │   │       |            |       ├── stats-filters/ # Sección inicial de filtra que afecta a los otros componentes para filtrar
│   │   │       |            |       |        ├── stats-filters.component.ts
│   │   │       |            |       |        ├── stats-filters.component.html
│   │   │       |            |       |        └── stats-filters.component.css
│   │   │       |            |       ├── timeline-chart/ # Línea de tiempo de acuerdo al filtrado
│   │   │       |            |       |        ├── timeline-chart.component.ts
│   │   │       |            |       |        ├── timeline-chart.component.html
│   │   │       |            |       |        └── timeline-chart.component.css
│   │   │       |            |       ├── top-countries-chart/ # Gráfica de barras top países
│   │   │       |            |       |        ├── top-countries-chart.component.ts
│   │   │       |            |       |        ├── top-countries-chart.component.html
│   │   │       |            |       |        └── top-countries-chart.component.css
│   │   │       |            |       └── violence-type-chart/ # Gráfica tipo dona para los tipos de violencia.
│   │   │       |            |                ├── violence-type-chart.component.ts
│   │   │       |            |                ├── violence-type-chart.component.html
│   │   │       |            |                └── violence-type-chart.component.css
│   │   │       |            |
│   │   │       |            ├── statistics.component.css
│   │   │       |            ├── statistics.component.html
│   │   │       |            └── statistics.component.ts # Sección de estadísticas
│   │   │       |
│   │   │       ├── explorer.component.css
│   │   │       ├── explorer.component.html
│   │   │       └── explorer.component.ts # Contiene toda la lógica para cargar las diferentes secciones
│   │   │
│   │   └── shared/
│   |       └── components/
│   |               ├──navbar/ # Barra superior
│   |               |    ├──navbar.component.ts
│   |               |    ├──navbar.component.html
│   |               |    └──navbar.component.cs
│   |               └──sidebar/ # Barra lateral
│   |                    ├──sidebar.component.ts
│   |                    ├──sidebar.component.html
│   |                    └──sidebar.component.css
│   │
│   ├── assets/                     # MARCADORES PARA MAPAS
│   │   ├── marker-icon-2x.png
│   │   ├── marker-icon.png
│   │   └── marker-shadow.png
│   │
│   ├── environments/  # Environment para producción.
│   │   ├── environment.ts
│   │   └── environment.prod.ts
│   │
|   ├── tailwing.config.js
│   ├── styles.css
│   ├── postcss.config.js
│   ├── main.ts
│   └── index.html
│
├── angular.json
├── package.json
├── package-lock.json
├── buildAndPush.bat
├── Dockerfile
├── nginx.conf
├── tailwind.config.js
├── tsconfig.app.jsson
└── tsconfig.json
```
