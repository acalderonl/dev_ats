/**
 * Si el formulario de un modal cambió desde que se abrió.
 *
 * Sirve para no preguntar «¿cerrar sin guardar?» cuando no hay nada que perder: la
 * pregunta solo tiene sentido si de verdad se escribió algo. Comparar por JSON basta
 * para los formularios de esta aplicación —objetos planos y arrays de objetos planos,
 * sin funciones ni fechas— y evita mantener un comparador campo por campo en cada
 * vista que podría desincronizarse del formulario real.
 */
export function huboCambios<T>(actual: T, inicial: T): boolean {
  return JSON.stringify(actual) !== JSON.stringify(inicial)
}

/**
 * Lo mismo, para un `Set` (por ejemplo, los permisos marcados de un rol).
 *
 * `JSON.stringify` de un `Set` da siempre `"{}"` —no mira su contenido—, así que
 * compararlos directo con `huboCambios` diría que nunca cambiaron. Se ordenan y se
 * convierten a array antes de comparar.
 */
export function huboCambiosEnSet(actual: Set<string>, inicial: Set<string>): boolean {
  return huboCambios([...actual].sort(), [...inicial].sort())
}
