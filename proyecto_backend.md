# Estructura Final del Proyecto - Arquitectura por Capas Simplificada

## 🏗️ BACKEND - Python/FastAPI

## ACTUALMENTE

```
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                              # Punto de entrada FastAPI
|   ├── config.py
│   │
│   │
│   ├── presentation/                        # 🔵 CAPA 1: PRESENTACIÓN
│   │   ├── __init__.py
│   │   │
│   │   └── routers/                         # ✅ Routing de endpoints
│   │       ├── __init__.py
│   │       ├── bigquery_router.py           # Rutas BigQuery
│   │       ├── neo4j_router.py              # Rutas Neo4j
│   │       ├── mongodb_router.py            # Rutas MongoDB
│   │       ├── conflict_map_router.py       # Router para redes de actores
│   │       ├── statistics_router.py         # Ruta para estadísticas
│   │       ├── dataflow_router.py           #Ruta para Dataflow
│   │       ├── summary.py                   # Ruta para Endpoints generales
│   │       └── health_router.py             # Health checks
│   │
│   ├── business/                            # 🟢 CAPA 2: LÓGICA DE NEGOCIO
│   │   ├── __init__.py
│   │   │
│   │   ├── services/                        # ✅ Servicios de negocio que utilizan los endpoints
│   │   │   ├── __init__.py
│   │   │   ├── bigquery_service.py          # Lógica BigQuery
│   │   │   ├── neo4j_service.py             # Lógica Neo4j
│   │   │   ├── mongodb_service.py           # Lógica MongoDB
│   │   │   ├── conflict_map_service.py      # Lógica para redes de actores
│   │   │   ├── statistics_service.py        # Lógica para statistics
│   │   │   └── dataflow_service.py          # Lógica para dataflow
│   │   │
│   │   └── models/                          # ✅ Domain Models
│   │       ├── __init__.py
|   |       └── schemas.py                   # Agrupa todos los esquemas
│   │
│   │
│   │
│   ├── integration/                         # 🟡 CAPA 3: INTEGRACIÓN - NO HAY NADA, TODO SE MANEJA EN LOS ANTERIORES SERVICIOS Y ROUTERS
│
├── requirements.txt                         # Dependencias Python
├── .env.example                             # Ejemplo de variables de entorno
├── .gitignore
├── Dockerfile                               # Docker para backend
├── docker-compose.yml                       # Compose para desarrollo
└── README.md

```

# Falta integrar controllers y integración /repositorios
