export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

type FastApiDetail = string | { msg: string }[] | undefined

function messageFrom(detail: FastApiDetail, status: number): string {
  if (typeof detail === 'string') return detail
  // FastAPI validation errors arrive as a list, one entry per invalid field.
  if (Array.isArray(detail) && detail.length > 0) return detail.map((d) => d.msg).join(' ')
  return status >= 500 ? 'Something went wrong on the server. Try again.' : 'Request failed.'
}

export async function api<T>(path: string, options: { method?: string; body?: unknown } = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      method: options.method ?? 'GET',
      credentials: 'same-origin',
      headers: options.body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(0, "Can't reach the server. Check that the backend is running.")
  }

  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => undefined)
  if (!response.ok) throw new ApiError(response.status, messageFrom(data?.detail, response.status))
  return data as T
}
