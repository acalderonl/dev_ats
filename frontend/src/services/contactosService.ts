import { apiGet } from '@/lib/apiClient'
import type { Contacto } from '@/types'

export const contactosService = {
  list: (filters?: { q?: string; nivel_instruccion?: string }) =>
    apiGet<Contacto[]>('/contactos', { params: filters }),
}
