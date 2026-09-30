# Especificación General y Objetivos del Sistema ATS (Applicant Tracking System)

## 1. Visión General del Proyecto y Objetivo
El objetivo de este proyecto es desarrollar desde cero un **Sistema de Seguimiento de Candidatos (ATS - Applicant Tracking System)** completo, intuitivo y moderno. La plataforma automatizará el ciclo de vida del reclutamiento y selección de talento, abarcando desde la creación de vacantes y su difusión multi-canal (LinkedIn API y WhatsApp) hasta la captura inteligente de currículums (parsing de PDF, DOC, DOCX), filtrado mediante preguntas automatizadas, pipeline de evaluación por etapas con autorizaciones, banco de contactos y administración de usuarios y roles.

### Atributos Clave del Sistema:
* **Ambiente Web Multiplataforma**: Diseño web totalmente *responsive* adaptado a dispositivos móviles, tablets y escritorios.
* **Experiencia de Usuario (UX/UI)**: Interfaz limpia, accesible, intuitiva, basada en principios de *Human-Centered Design* con soporte para vistas Kanban y tablas interactivas.
* **Stack Tecnológico Principal**:
  * **Backend**: Python 3.12+ (Framework web como FastAPI / Django REST Framework con enfoque en arquitectura limpia y cumplimiento de PEP 8).
  * **Base de Datos**: PostgreSQL 16+ para almacenamiento relacional robusto, integridad referencial y soporte JSONB para estructuración flexible de cvs y evaluaciones.
  * **Frontend**: SPA o SSR moderno con soporte de componentes interactivos y diseño responsive adaptativo.
  * **Orquestación y Entorno Contenerizado**: **Docker y Docker Compose** para empaquetar y gestionar todo el ecosistema (PostgreSQL, Backend Python y Frontend) de manera unificada con un único comando execution (`docker compose up --build`).

---

## 2. Arquitectura de Módulos y Requerimientos Funcionales

```
+-----------------------------------------------------------------------------------+
|                                  SISTEMA ATS                                      |
+-----------------------------------------------------------------------------------+
|  [Módulo 1] Creación de Vacantes, Cargos e Integraciones (LinkedIn / WhatsApp)   |
|  [Módulo 2] Portal Público del Postulante (Parsing CV + Preguntas Filtro)        |
|  [Módulo 3] Pipeline de Reclutamiento y Gestión de Estados                       |
|  [Módulo 4] Directorio y Gestión de Contactos (Postulantes)                     |
|  [Módulo 5] Módulo de Evaluaciones y Calificaciones                               |
|  [Módulo 6] Dashboard Central (Home / Métricas)                                  |
|  [Módulo 7] Administración de Usuarios, Autenticación y Roles (RBAC)            |
+-----------------------------------------------------------------------------------+
|  [Infraestructura] Docker & Docker Compose (PostgreSQL + Python Backend + Front)  |
+-----------------------------------------------------------------------------------+
```

---

### Módulo 1: Gestión de Cargos, Creación de Vacantes e Integraciones Externas

#### 1.1 Gestionar Cargos (Catálogo Base)
* **Objetivo**: Administrar el catálogo de cargos organizacionales a los cuales se vincularán las preguntas filtro y las vacantes.
* **Funcionalidades**:
  * CRUD completo de Cargos (Crear, Leer, Actualizar, Desactivar).
  * Asignación de categoría, área o departamento.
  * Plantillas de preguntas filtro asociadas por defecto a cada cargo.

#### 1.2 Preguntas Filtro por Cargo (Employer Filtering Questions)
* **Objetivo**: Permitir al empleador definir preguntas clave de descarte o puntuación.
* **Funcionalidades**:
  * Creación de preguntas tipo: Selección múltiple, Opción única, Texto libre, Numérico, Si/No.
  * Categorización por Cargo: Toda pregunta pertenece estrictamente a un Cargo específico.
  * Definición de respuestas correctas, ponderaciones o criterios de eliminación automática (*knockout questions*).

#### 1.3 Creación y Publicación de Vacantes
* **Objetivo**: Publicar ofertas laborales adjuntando documentación técnica o descriptiva y generando enlaces únicos.
* **Funcionalidades**:
  * Carga de documentos descriptivos del puesto en formato `.pdf`, `.docx` o `.doc`.
  * Definición de fecha límite / caducidad de la vacante.
  * Generación automática de enlace único público (*slug* parametrizado) para la postulación.
  * **Conexión con LinkedIn API**:
    * Publicación automática de la oferta cumpliendo estrictamente los parámetros exigidos por la API de LinkedIn (Job Posting API: título, descripción, ubicación, tipo de empleo, URL de aplicación externa/captura).
    * Captura del ID del post de LinkedIn para métricas de trazabilidad.
  * **Compartición en WhatsApp**:
    * Generación de botón/enlace rápido para compartir la oferta vía WhatsApp Web/App con mensaje preformateado y enlace directo.

---

### Módulo 2: Portal Público del Postulante y Parsing de Documentos

#### 2.1 Vista de Postulación Pública
* **Objetivo**: Permitir al candidato visualizar la oferta y postularse mediante un formulario dinámico e inteligente.
* **Funcionalidades**:
  * Acceso mediante el link generado en la vacante (capturado desde la publicación en LinkedIn / WhatsApp).
  * Visualización detallada de la oferta laboral.

#### 2.2 Carga de Currículum y Parsing Automático
* **Objetivo**: Extraer la información estructurada del CV cargado por el postulante sin requerir tipeo manual repetitivo.
* **Soporte de Formatos**: Archivos `.pdf`, `.docx` y `.doc`.
* **Motor de Parsing ATS**: Analiza el documento y auto-completa los siguientes campos en el formulario:
  1. Nombres
  2. Apellidos
  3. Edad
  4. Número de Cédula / Identificación
  5. Formación Secundaria (Institución, Título obtenido, Año de finalización)
  6. Formación Superior (Universidad/Instituto, Título obtenido, Estado)
  7. Nivel de Instrucción (Técnico, Tecnológico, Tercer Nivel, Cuarto Nivel / Posgrado)
  8. Títulos Obtenidos
  9. Experiencia Laboral Detallada:
     * Cargo desempeñado
     * Empresa
     * Fecha de inicio (Desde)
     * Fecha de fin (Hasta) o indicador de "Actualmente trabajando aquí"
* **Revisión del Postulante**: El formulario auto-llenado permite al postulante verificar y corregir datos extraídos antes de enviar.

#### 2.3 Formulario de Preguntas Filtro
* Presentación dinámica de las preguntas filtro asignadas por el empleador para el cargo de la vacante.
* Registro obligatorio de respuestas previo al envío definitivo de la postulación.

#### 2.4 Control de Caducidad de Vacante y Landing Page de Expiración
* **Lógica de Expiración**: Verificación en tiempo real de la fecha límite de la vacante.
* **Landing Page de Vacante Expirada**: Si el enlace es accedido después de la fecha de caducidad, el sistema redirige automáticamente a una página dedicada con:
  * Mensaje claro: *"Esta vacante ha expirado. Lo sentimos, revisa nuestro LinkedIn para más información."*
  * Fotografía/Logo de la empresa enlazado directamente al perfil principal de LinkedIn corporativo.

---

### Módulo 3: Pipeline de Reclutamiento y Gestión de Estados

#### 3.1 Flujo de Trabajo y Etapas de Postulación
* **Estados del Pipeline**:
  1. `Postulación Revisada`
  2. `En Revisión`
  3. `Preseleccionado`
  4. `Evaluaciones`
  5. `Entrevista`
  6. `Contratado` / `Descartado`

#### 3.2 Regla de Autorización y Pre-Chequeo
* **Condición Estricta**: Ninguna postulación puede ingresar o avanzar en este módulo de tratamiento de vacantes sin haber sido **previamente chequeada y autorizada** por un reclutador/autorizador responsable.
* Registro de auditoría (*log*) con usuario, fecha y hora de la autorización.

#### 3.3 Interfaz de Gestión (Vista Kanban / Tabla)
* Arrastrar y soltar (*drag-and-drop*) para mover candidatos entre estados autorizados.
* Filtros por vacante, puntuación de coincidencia de CV, respuestas a preguntas filtro y estado.

---

### Módulo 4: Directorio y Gestión de Contactos (Talent Pool)

* **Objetivo**: Centralizar la base de datos de todos los postulantes que han aplicado históricamente al sistema.
* **Funcionalidades**:
  * Vista en formato de tabla de contactos/seguidos.
  * Campos visibles: Nombre completo, Cédula, Correo, Teléfono, Nivel de instrucción, Último cargo, Estado acumulado y Vacantes a las que ha postulado.
  * Búsqueda avanzada por palabras clave, habilidades, títulos y rango de experiencia.
  * Opciones de gestión: Exportar datos, etiquetar candidato, enviar correo masivo/individual, reasignar a nuevas vacantes.

---

### Módulo 5: Módulo de Evaluaciones

* **Objetivo**: Almacenar y gestionar de forma reservada los resultados de las evaluaciones aplicadas a los candidatos.
* **Funcionalidades**:
  * Registro de pruebas psicométricas, técnicas, entrevistas y evaluaciones de desempeño.
  * Puntuación consolidada (*scorecard*) por candidato.
  * Repositorio de observaciones confidenciales del equipo de selección.
  * Trazabilidad vinculada al perfil del postulante en el Módulo de Contactos.

---

### Módulo 6: Dashboard Central (Home / Panel de Control)

* **Objetivo**: Servir como pantalla principal (Home) agrupando métricas operativas y analíticas del ATS.
* **Métricas Principales**:
  * Total de vacantes activas vs. expiradas.
  * Volumen de postulaciones recibidas (por día, semana, mes).
  * Distribución de postulantes por etapa del pipeline.
  * Tasa de conversión de LinkedIn vs. WhatsApp.
  * Próximas entrevistas y actividades pendientes.

---

### Módulo 7: Configuraciones, Administración de Usuarios y Roles (RBAC)

* **Objetivo**: Administrar el acceso al sistema, registro de usuarios y asignación de permisos.
* **Funcionalidades**:
  * **Registro de Usuarios por Correo**: Autenticación segura y registro almacenado en PostgreSQL.
  * **Control de Acceso Basado en Roles (RBAC)**:
    * *Super Admin*: Acceso total y configuración del sistema.
    * *Reclutador / Empleador*: Creación de vacantes, gestión de preguntas filtro, evaluación de candidatos y autorización.
    * *Entrevistador / Evaluador*: Acceso restringido a evaluaciones y notas.
  * Registro de actividad y seguridad (encriptación de contraseñas con bcrypt/argon2, manejo de tokens JWT).

---

## 3. Modelo de Datos y Esquema de Base de Datos (PostgreSQL)

```sql
-- Esquema simplificado de entidades en PostgreSQL

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    rol_id INT REFERENCES roles(id),
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cargos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    departamento VARCHAR(100),
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE preguntas_filtro (
    id SERIAL PRIMARY KEY,
    cargo_id INT REFERENCES cargos(id) ON DELETE CASCADE,
    pregunta TEXT NOT NULL,
    tipo_respuesta VARCHAR(50) NOT NULL, -- 'multiple', 'unica', 'texto', 'booleano', 'numero'
    opciones JSONB, -- Opciones posibles si aplica
    es_eliminatoria BOOLEAN DEFAULT FALSE,
    respuesta_correcta TEXT
);

CREATE TABLE vacantes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo VARCHAR(200) NOT NULL,
    cargo_id INT REFERENCES cargos(id),
    descripcion TEXT NOT NULL,
    documento_adjunto_url VARCHAR(500),
    slug VARCHAR(250) UNIQUE NOT NULL,
    fecha_limite TIMESTAMP NOT NULL,
    linkedin_post_id VARCHAR(100),
    empleador_id UUID REFERENCES usuarios(id),
    estado VARCHAR(50) DEFAULT 'activa', -- 'activa', 'expirada', 'cerrada'
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE postulantes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    telefono VARCHAR(50),
    edad INT,
    formacion_secundaria JSONB,
    formacion_superior JSONB,
    nivel_instruccion VARCHAR(100),
    titulos TEXT[],
    experiencia_laboral JSONB, -- Array de objetos con empresa, cargo, fecha_desde, fecha_hasta, actualmente
    cv_documento_url VARCHAR(500) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE postulaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vacante_id UUID REFERENCES vacantes(id),
    postulante_id UUID REFERENCES postulantes(id),
    respuestas_filtro JSONB,
    autorizado_por UUID REFERENCES usuarios(id),
    fecha_autorizacion TIMESTAMP,
    estado_pipeline VARCHAR(50) DEFAULT 'pendiente_autorizacion', -- 'postulacion_revisada', 'en_revision', 'preseleccionado', 'evaluaciones', 'entrevista', 'contratado', 'descartado'
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE evaluaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    postulacion_id UUID REFERENCES postulaciones(id) ON DELETE CASCADE,
    evaluador_id UUID REFERENCES usuarios(id),
    tipo_evaluacion VARCHAR(100) NOT NULL,
    puntaje NUMERIC(5,2),
    observaciones TEXT,
    documentos_evaluación JSONB,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Instrucciones para la Implementación Autónoma con Claude Code & Docker

Para garantizar una construcción impecable y sin errores desde la primera ejecución completa con Claude:

1. **Orquestación con Docker Compose**:
   * Claude deberá estructurar los archivos `docker-compose.yml`, `backend/Dockerfile` y `frontend/Dockerfile`.
   * Todo el entorno (Base de Datos PostgreSQL con healthchecks, Backend Python FastAPI/DRF y Frontend Web) debe iniciarse mediante `docker compose up --build`.
2. **Estrategia Vertical por Funcionalidad (Vertical Slices)**:
   * No implementes capas horizontales aisladas. Desarrolla cada módulo de extremo a extremo (Base de Datos -> API Backend -> UI Frontend -> Pruebas) dentro de los contenedores antes de pasar al siguiente.
3. **Configuración de `CLAUDE.md`**:
   * Mantén el archivo `CLAUDE.md` en la raíz registrando los comandos de Docker Compose (`docker compose exec backend pytest`, `docker compose up`, etc.) y las convenciones PEP 8 & Clean Code.
4. **Manejo Estricto de Errores y Calidad de Código**:
   * Sigue las recomendaciones de *Clean Code* (Robert C. Martin): funciones cortas, responsabilidad única (SRP), separación explícita de manejo de excepciones y eliminación de código duplicado.
5. **Verificación Autónoma**:
   * Ejecuta pruebas unitarias e integración automáticamente dentro del contenedor backend. Valida endpoints REST y formularios interactivos antes de marcar cada módulo como completado.
