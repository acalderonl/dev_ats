# El formulario del candidato — mapeo campo por campo

Qué pide el formulario, dónde se guarda, y qué intenta sacar del CV el lector automático.

La fuente es `docs/resouces/ESQUEMA FORMULARIO PARA APLICANTE ATS.docx`: ocho capturas de la
pantalla de postulación de Hiring Room. Este documento es su traducción a nuestras tablas, y es
también **el contrato del robot de ETL**: lo que extraiga tiene que caber en estas columnas.

> El `.docx` no tiene texto: son imágenes. Si hace falta volver a mirarlo, se descomprime
> (`unzip`) y las capturas están en `word/media/`.

## Las dos pantallas

| | Paso | Qué hace |
|---|---|---|
| 1 | Datos personales | Identidad y contacto, con la foto. Todo obligatorio |
| 2 | Información adicional | Educación, idiomas, experiencia, redes, adjunto y expectativas |

**El formulario no lee el CV.** Hubo un paso previo que lo subía y rellenaba el resto con lo
extraído; se quitó porque **eso lo hace el robot de ETL**. Quien llegue al portal escribe sus
datos, y por eso lo que entra por aquí se guarda siempre con `origen_datos = manual`.

El candidato sí puede **adjuntar** su currículum en el paso 2: eso es conservar el archivo, no
leerlo, y nadie más lo hace por él.

## Paso 1 · Datos personales → tabla `postulantes`

| Campo en pantalla | Columna | Control | Oblig. | ¿Lo busca el lector de CV? |
|---|---|---|---|---|
| Foto | `foto_url` | Subida de imagen | No | No |
| Nombre | `nombres` | Texto | **Sí** | Sí |
| Apellido | `apellidos` | Texto | **Sí** | Sí |
| Email | `email` | Texto | **Sí** | Sí |
| Confirmar email | — | Texto | **Sí** | No se guarda: solo comprueba que no haya un dedazo |
| Tipo de documento | `tipo_documento` | Selector cerrado | **Sí** | Sí |
| N.º de documento | `cedula` | Texto | **Sí** | Sí |
| Teléfono (código) | `telefono_codigo_pais` | Texto, por defecto `+593` | **Sí** | Sí |
| Teléfono | `telefono` | Texto | **Sí** | Sí |
| Tipo de teléfono | `telefono_tipo` | Selector cerrado | **Sí** | Sí |
| Género | `genero` | Selector cerrado | **Sí** | Sí |
| Nacionalidad | `nacionalidad` | Sugerido | **Sí** | Sí |
| País de residencia | `pais_residencia` | Sugerido | **Sí** | Sí |
| Provincia | `provincia` | Sugerido | **Sí** | Sí |
| Localidad | `localidad` | Texto | **Sí** | Sí |
| Fecha de nacimiento | `fecha_nacimiento` | Día + mes + año | **Sí** | Sí |
| (calculado) | `edad` | — | — | Sale de la fecha, no se pregunta |

## Paso 2 · Información adicional

### Educación → tabla `postulante_educacion` (una fila por título)

`titulo` · `pais` · `institucion` · `area_estudio` · `nivel_estudio` · `estado_estudio` ·
`inicio_mes` + `inicio_anio` · `actualmente` · `fin_mes` + `fin_anio` · `descripcion`

Más, en `postulantes`:

- `estudios_secundarios_completos` — la pregunta de sí/no.
- `nivel_instruccion` — **no se pregunta**: lo calcula el servidor con el nivel más alto de la
  lista. Es una copia a propósito, porque el directorio de contactos filtra por él en cada
  búsqueda y bajar a la tabla cada vez saldría más caro.

### Idiomas → tabla `postulante_idiomas`

`idioma` · `nivel_escrito` · `nivel_oral`

### Experiencia laboral → tabla `postulante_experiencia` (una fila por trabajo)

`puesto` · `jerarquia` · `empresa` · `pais` · `industria` · `area_trabajo` · `subarea_trabajo` ·
`inicio_mes` + `inicio_anio` · `actualmente` · `fin_mes` + `fin_anio` · `descripcion`

### Lo demás → `postulantes`

| Campo en pantalla | Columna | Nota |
|---|---|---|
| LinkedIn | `linkedin_url` | |
| Otras redes | `otras_redes` (JSONB) | `[{red, url}]`. Lista abierta: no merece una tabla |
| Currículum adjunto | `cv_documento_url` | Máx. 15 MB; PDF, DOCX, JPG o PNG |
| Expectativas personales | `expectativas` | |
| Acepto la política | `acepto_privacidad_en` | Se guarda **cuándo**, no solo que sí: sin la fecha no se puede demostrar qué versión aceptó |
| (interno) | `origen_datos` | El formulario manda siempre `manual`. `cv` queda para las fichas que cree el robot de ETL |

Las preguntas filtro de la vacante, si las hay, se guardan en la postulación
(`postulaciones.respuestas_filtro`), no en la ficha: son de esa vacante, no de la persona.

## Dos decisiones que no son obvias

**Selector cerrado o campo con sugerencias.** Donde el conjunto es cerrado —género, nivel de
estudio, jerarquía, nivel de idioma— hay un `<select>`: lo que no está en la lista no es un dato
que falte, es un dato que no existe. Donde la lista es abierta —país, institución, idioma,
industria, área— hay un campo con sugerencias (`<datalist>`): se ofrece lo frecuente y se acepta
cualquier cosa. El esquema de referencia usa selectores también ahí; mantener a mano las 195
nacionalidades, las universidades del mundo o todas las ciudades sería prometer una lista
completa que nunca lo estaría, y dejaría fuera a una persona real. Las sugerencias están en
`frontend/src/lib/catalogosDelFormulario.ts`.

**Mes y año, sin día.** Un CV dice «Junio 2019», casi nunca «7 de junio». Guardar una fecha
completa obligaría a inventarse el día. Las únicas fechas con día son la de nacimiento, que sí
se pregunta entera, y las que pone el sistema.

## Dónde van los archivos, y quién puede verlos

La foto y el CV son **datos personales**, así que no comparten camino con la imagen de un post:

- Se guardan en `media_data/postulantes/`.
- Salen por `GET /api/v1/archivos/postulantes/{nombre}`, que **pide sesión**.
- `GET /api/v1/media/...` —que va sin autenticación porque LinkedIn tiene que poder leer la
  imagen de un post— **se niega a servir esa carpeta**. Hay una prueba que lo comprueba.

El candidato nunca necesita esa ruta: ve su foto desde el archivo que acaba de elegir.

## Lo que falta

- **El robot de ETL.** Es quien tiene que leer el CV y rellenar estos campos; el formulario ya
  no lo intenta. La pieza que hoy existe, `extraccion_cv_service`, manda el archivo a Claude y
  devuelve exactamente este esquema, y sin clave configurada cae a unas heurísticas que sacan
  cuatro campos y lo dicen. El robot la sustituirá o se apoyará en ella; el contrato es esta
  tabla.
- 🔴 **`POST /api/v1/public/leer-cv` se quedó sin quien la llame** y sigue abierta sin
  autenticación. Cada llamada cuesta dinero en la API de Claude; el límite por IP la protege,
  pero ya no hay tráfico legítimo anónimo. Cuando se sepa cómo se identifica el robot, lo
  sensato es cerrarla con sesión.
- **Los archivos huérfanos.** Si alguien sube una foto y abandona el formulario, el archivo se
  queda. No estorba, pero nadie lo borra todavía.
- **Borrar los datos de un candidato a petición** (fase S.5). Hace falta antes de que entren
  personas reales.
