const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
const AUTH_STORAGE_KEY = 'ats-auth'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function getToken(): string | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed?.state?.token ?? null
  } catch {
    return null
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    window.dispatchEvent(new Event('ats:unauthorized'))
  }
  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    throw new ApiError(response.status, typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

function authHeaders(): HeadersInit {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

interface RequestOptions {
  params?: Record<string, string | number | boolean | undefined>
}

function buildUrl(path: string, params?: RequestOptions['params']): string {
  const url = new URL(`${API_BASE_URL}${path}`)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value))
    }
  }
  return url.toString()
}

export async function apiGet<T>(path: string, options?: RequestOptions): Promise<T> {
  const response = await fetch(buildUrl(path, options?.params), { headers: { ...authHeaders() } })
  return handleResponse<T>(response)
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(buildUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  return handleResponse<T>(response)
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(buildUrl(path), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  return handleResponse<T>(response)
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(buildUrl(path), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  return handleResponse<T>(response)
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(buildUrl(path), { method: 'DELETE', headers: { ...authHeaders() } })
  return handleResponse<T>(response)
}

export async function apiUpload<T>(path: string, file: File): Promise<T> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(buildUrl(path), { method: 'POST', headers: { ...authHeaders() }, body: formData })
  return handleResponse<T>(response)
}
