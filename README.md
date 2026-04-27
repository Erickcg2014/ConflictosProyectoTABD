# ⚔️ PROYECTO TABD - APLICACIÓN WEB HISTÓRICO DE GUERRAS

Este proyecto implementa un **sistema de visualización para análisis** en base a datos históricos de guerra con las siguientes herramientas utilizadas:

- **Frontend Angular** servido con Nginx
- **Backend en Python** (Fast API / API REST)
- **Base de datos BigQuery** Bases de datos Columnar para consultas analíticas y gráficos
- **Base de datos Neo4j** Bases de datos de Grafos para consultas por grafos
- **Base de datos MongoDB** Bases de datos Geográfica para localizaciones de los países involucrados
- **Apache Airflow** Servicio ETL para la carga de datos y actualizaciones en las BD's
- **Orquestación completa** con pods de Kubernetes

## Todo esto configurado con imagenes **Docker** (Excepto herramientas en nube como **BigQuery y MongoDB**) en un almacén de imágenes (**Registry**) orquestado con **Kubernetes**

## 🚀 Requisitos Previos

Antes de empezar, asegurarse de tener instalado:

- 🐳 [Docker](https://www.docker.com/get-started)
- ☸️ Habilitar la extensión de Kubernetes del docker desktop (**Enable Kubernetes**)

---

## Datos iniciales

- Está parte todavía no está definida

## Fases del proyecto - Instalación

Para el proceso de instalación y configuración, debe abrir una terminal (CMD) y ingrese en la raíz de la carpeta del proyecto llamada (**PROYECTO_TABD**) para escribir los comandos y ejecutarlos.

### Fase Inicial: Construir Todo el Proyecto

Lo primero que debe hacer, es configurar un **ingress-controller** para el frontend del proyecto

1. En la raíz del proyecto, ejecute lo siguiente:

```env
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

2. Posterior a ello, vamos a configurar un nombre de espacio para este proyecto

```env
kubectl create namespace wars
```

3. En el siguiente paso, defina un registry para almacenar las imágenes:

```env
docker run -d -p 5000:5000 --name registry registry:2.7
```

4. Por último, inicie el registry (aunque por efecto anterior ya debería estar inicializado)

```env
 docker start registry
```

### Fase intermedia: Ejecutar las configuraciones necesarias

**NOTA:** En cada carpeta del proyecto se encuentran buildAndPush definidos para cargar las imágenes al registry creado. Los nombres de las imágenes se pasan por parametro a través de la consola, están definidas de acuerdo a las instrucciones siguiente.

Se debe ingresar a cada carpeta y ejecutar los .bat de la siguiente manera.

---

Realice los siguientes pasos:

1. Ingrese a la carpeta demo del **Backend.**

```env
cd Back
```

**Ejecute lo siguiente:**

```env
buildAndPush.bat wars-backend
```

2.  Ingrese a la carpeta del **Frontend**

```env
cd frotend/angular-frontend
```

**Ejecute lo siguiente:**

```env
buildAndPush.bat wars_frontend
```

3. En la carpeta **Airflow**

```env
cd airflow
```

**Ejecute lo siguiente:**

```env
buildAndPush.bat airflow
```

4. En la carpeta **postgres_airflow**

```env
cd postgres_airflow
```

**Ejecute lo siguiente:**

```env
buildAndPush.bat wars-postgres
```

### Fase final: Aplicar configuraciones k8s

Ahora, ubicandose en la **raíz del proyecto**, ingrese a la carpeta **k8s**

```env
cd k8s
```

Y ejecute lo siguiente:

```env
aplicar_configuraciones_k8s.bat
```

Posterior a esto, y habiendo finalizado los pasos, ya puede trabajar con los pods

## Visualización y manejo de pods

- Para **visualizar** los pods y **sus nombres**, todos deben aparecer todos en **STATUS: RUNNING y READY**

```env
kubectl get pods -n wars
```

- Para **borrar** los pods (actualizaciones de código o de k8s)

```env
kubectl delete --all pods -n wars
```

- Para **logs** de cualquier de los pods, cambiele el nombre por el nombre del pod que desee visualizar

```env
kubectl logs <name-pod> -n wars
```

- Si quiere una **vista detallada y específica** de un pod

```env
kubectl describe pod <name-pod> -n wars
```

### Actualizaciones o cambios

En dado caso que tenga que actualizar o cambiar algunas partes del código, tendrá que volver a desplegar con lo siguientes comandos

---

1. Si realizo un cambio en **algun archivo de las carpetas de proyecto** (Tanto de Backend, Frontend, airflow, etc), **ejecute el BuildAndPush vistos anteriormente en la FASE INTERMEDIA** en la carpeta correspondiente del cambio.

- **A manera de ejemplo:** Si realice cambios en el Frontend, entro a la carpeta Frontend/Angular-frontend y ejecuto el **buildAndPush.bat wars_frontend** para actualizar la imagen del registro.

2. Si realizo un cambio en algún **deployment**, **ingresé a la carpeta K8S** en la terminal y ejecuté nuevamente

```env
aplicar_configuraciones_k8s.bat
```

3. Después ejecute borrado de los pods para actualizar los cambios.

```env
kubectl delete --all pods -n wars
```

4. Obtenga y visualice nuevamente los pods. Debe aparecerle igualmente todos en **STATUS: RUNNING**

```env
kubectl get pods -n wars
```

### Volver a ejecutar

Siempre que tenga que volver a inicializar los pods **(comunmente cuando apague su pc y vuelva a prenderla)** recuerde iniciar su registry y volver a instalar los pods.

```env
 docker start registry
```

**borrar** los pods viejos (se actualiza tomando las imágenes previamente cargadas al registry)

```env
kubectl delete --all pods -n wars
```

El automáticamente recrea los pods actualizando las imágenes del registry, lo puede comprobar ejecutando:

```env
kubectl get pods -n wars
```

Y todos deben estar **STATUS: RUNNING**

## Comandos útiles para liminar

Si desea eliminar todos los recursos excepto PVC:

```env
kubectl delete all --all -n wars
```

```env
kubectl delete pvc --all -n wars
```
