const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

interface ApiFileResponse {
  blob: Blob
  filename: string
  contentType: string
}

function jsonHeaders(body?: unknown): HeadersInit | undefined {
  return body === undefined ? undefined : { 'Content-Type': 'application/json' }
}

async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text()
  if (!text) return `API error: ${res.status}`

  try {
    const payload = JSON.parse(text) as { detail?: unknown }
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const detail = payload.detail
      return typeof detail === 'string' ? detail : JSON.stringify(detail)
    }
    return typeof payload === 'string' ? payload : text
  } catch {
    return text
  }
}

function parseFilename(contentDisposition: string | null): string | undefined {
  if (!contentDisposition) return undefined

  const utf8Match = contentDisposition.match(/filename\*\s*=\s*UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1].trim().replace(/^"|"$/g, ''))
  }

  const plainMatch = contentDisposition.match(/filename\s*=\s*"?([^";]+)"?/i)
  if (plainMatch?.[1]) {
    return plainMatch[1].trim()
  }

  return undefined
}

async function requestJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init)
  if (!res.ok) throw new Error(await readErrorMessage(res))
  return res.json() as Promise<T>
}

async function requestFile(
  path: string,
  init: RequestInit = {},
): Promise<ApiFileResponse> {
  const res = await fetch(`${API_BASE}${path}`, init)
  if (!res.ok) throw new Error(await readErrorMessage(res))

  const blob = await res.blob()
  return {
    blob,
    filename: parseFilename(res.headers.get('content-disposition')) || 'download',
    contentType: res.headers.get('content-type') || blob.type || 'application/octet-stream',
  }
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.rel = 'noopener'
  document.body.appendChild(link)
  link.click()
  link.remove()

  window.setTimeout(() => {
    URL.revokeObjectURL(url)
  }, 1000)
}

export async function apiGet<T>(path: string): Promise<T> {
  return requestJson<T>(path)
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: 'POST',
    headers: jsonHeaders(body),
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: 'PUT',
    headers: jsonHeaders(body),
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

export async function apiPostFile(path: string, body?: unknown): Promise<ApiFileResponse> {
  return requestFile(path, {
    method: 'POST',
    headers: jsonHeaders(body),
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

export async function apiGetFile(path: string): Promise<ApiFileResponse> {
  return requestFile(path)
}

export async function apiDelete(path: string): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(await readErrorMessage(res))
}
