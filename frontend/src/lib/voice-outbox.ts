/** Recordings waiting to be uploaded, kept in the phone's IndexedDB so none are lost to a weak
 * signal, a closed tab or a dead battery: a recording is saved here the moment it stops, and only
 * removed once the server has confirmed it. The server ignores a repeat of the same client_id, so
 * retrying an upload that actually got through is harmless. */

export type OutboxItem = {
  clientId: string
  requestId: number
  blob: Blob
  createdAt: number
  // Set when the server refused the upload outright (a 4xx), so retrying wouldn't help.
  rejected?: string
}

const DB_NAME = 'sollu-voice'
const STORE = 'outbox'

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1)
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: 'clientId' })
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

async function run<T>(mode: IDBTransactionMode, action: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await openDb()
  try {
    return await new Promise<T>((resolve, reject) => {
      const request = action(db.transaction(STORE, mode).objectStore(STORE))
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  } finally {
    db.close()
  }
}

export async function listOutbox(requestId: number): Promise<OutboxItem[]> {
  const all = await run<OutboxItem[]>('readonly', (store) => store.getAll())
  return all.filter((item) => item.requestId === requestId).sort((a, b) => a.createdAt - b.createdAt)
}

export function saveToOutbox(item: OutboxItem): Promise<IDBValidKey> {
  return run('readwrite', (store) => store.put(item))
}

export function removeFromOutbox(clientId: string): Promise<undefined> {
  return run('readwrite', (store) => store.delete(clientId))
}

export function newClientId(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`
}
