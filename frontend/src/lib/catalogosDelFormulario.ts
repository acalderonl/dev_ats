/**
 * Las opciones del formulario de postulación.
 *
 * Dos clases de campo, y la diferencia importa:
 *
 * - **Conjunto cerrado** (género, nivel de estudio, jerarquía...): un `<select>`. Lo
 *   que no esté en la lista no es un dato que falte, es un dato que no existe.
 * - **Lista abierta** (país, institución, idioma, industria...): un `<input>` con
 *   `<datalist>`. Sugiere lo frecuente sin cerrar la puerta: mantener a mano las
 *   195 nacionalidades, las universidades del mundo o todas las ciudades sería
 *   prometer una lista completa que nunca lo estaría, y dejaría fuera a quien no
 *   aparezca. El esquema de referencia usa selectores; aquí se prefiere no perder
 *   datos de una persona real.
 */

export const TIPOS_DE_DOCUMENTO = ['Cédula', 'Pasaporte', 'RUC', 'Carné de refugiado'] as const

export const TIPOS_DE_TELEFONO = ['Celular/Móvil', 'Fijo', 'Trabajo'] as const

export const GENEROS = ['Masculino', 'Femenino', 'Otro', 'Prefiero no decirlo'] as const

/** Orden de menor a mayor: el resumen del directorio de contactos usa el más alto. */
export const NIVELES_DE_ESTUDIO = [
  'Secundaria',
  'Técnico',
  'Universitario',
  'Máster',
  'Posgrado',
  'Doctorado',
] as const

export const ESTADOS_DE_ESTUDIO = ['Graduado', 'En curso', 'Incompleto'] as const

export const JERARQUIAS = ['Junior', 'Semi-Senior', 'Senior', 'Jefatura', 'Dirección'] as const

export const NIVELES_DE_IDIOMA = ['Básico', 'Intermedio', 'Avanzado', 'Nativo'] as const

export const MESES = [
  'Enero',
  'Febrero',
  'Marzo',
  'Abril',
  'Mayo',
  'Junio',
  'Julio',
  'Agosto',
  'Septiembre',
  'Octubre',
  'Noviembre',
  'Diciembre',
] as const

/** Las 24 de Ecuador. Quien resida fuera escribe la suya: el campo no está cerrado. */
export const PROVINCIAS_DE_ECUADOR = [
  'Azuay',
  'Bolívar',
  'Cañar',
  'Carchi',
  'Chimborazo',
  'Cotopaxi',
  'El Oro',
  'Esmeraldas',
  'Galápagos',
  'Guayas',
  'Imbabura',
  'Loja',
  'Los Ríos',
  'Manabí',
  'Morona Santiago',
  'Napo',
  'Orellana',
  'Pastaza',
  'Pichincha',
  'Santa Elena',
  'Santo Domingo de los Tsáchilas',
  'Sucumbíos',
  'Tungurahua',
  'Zamora Chinchipe',
] as const

/** Sugerencias, no la lista del mundo. Ecuador primero porque es donde está la ANAI. */
export const PAISES_SUGERIDOS = [
  'Ecuador',
  'Colombia',
  'Perú',
  'Venezuela',
  'Argentina',
  'Chile',
  'Bolivia',
  'Brasil',
  'México',
  'España',
  'Estados Unidos',
  'Cuba',
  'Uruguay',
  'Paraguay',
  'Panamá',
  'Costa Rica',
] as const

export const IDIOMAS_SUGERIDOS = [
  'Español',
  'Inglés',
  'Francés',
  'Portugués',
  'Alemán',
  'Italiano',
  'Quichua',
  'Mandarín',
] as const

export const AREAS_DE_TRABAJO_SUGERIDAS = [
  'Administración y Finanzas',
  'Atención al Cliente',
  'Comercial y Ventas',
  'Educación, Docencia e Investigación',
  'Legal',
  'Logística y Operaciones',
  'Marketing y Comunicación',
  'Producción y Mantenimiento',
  'Recursos Humanos y Capacitación',
  'Salud',
  'Tecnología y Sistemas',
] as const

export const INDUSTRIAS_SUGERIDAS = [
  'Educación',
  'Salud',
  'Comercio',
  'Industria y Manufactura',
  'Construcción',
  'Servicios Financieros',
  'Tecnología',
  'Transporte y Logística',
  'Turismo y Hotelería',
  'Sector Público',
  'ONG y Fundaciones',
] as const

export const AREAS_DE_ESTUDIO_SUGERIDAS = [
  'Administración',
  'Ciencias de la Educación',
  'Comunicación',
  'Contabilidad y Auditoría',
  'Derecho',
  'Diseño',
  'Economía',
  'Enfermería',
  'Ingeniería Civil',
  'Ingeniería Industrial',
  'Marketing',
  'Medicina',
  'Psicología',
  'Recursos Humanos / Relac. Ind.',
  'Sistemas e Informática',
] as const

/** El año en curso y hacia atrás: nadie estudió en el futuro, pero sí termina en él. */
export function anios(desde = 1960, hastaAdelante = 8): number[] {
  const ahora = new Date().getFullYear()
  const lista: number[] = []
  for (let a = ahora + hastaAdelante; a >= desde; a--) lista.push(a)
  return lista
}
