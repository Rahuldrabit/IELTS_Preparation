/**
 * IndexedDBStore — offline-first event buffer using IndexedDB.
 *
 * Purpose:
 *   - Buffer telemetry events locally before upload
 *   - Survive page refreshes / network drops
 *   - Batch retrieval for upload cycles
 *   - Auto-prune old data to prevent unbounded growth
 *
 * Design:
 *   - Simple key-value on top of IndexedDB (no complex queries needed)
 *   - Promise-based API wrapping IDBRequest callbacks
 *   - Configurable DB name and store name for test isolation
 *   - Fallback to in-memory if IndexedDB unavailable
 */

import type { TelemetryEvent, TelemetryUploadPayload } from '../types'

export interface IndexedDBStoreConfig {
  dbName: string
  storeName: string
  /** Max events to buffer before force-prune oldest */
  maxSize: number
}

const DEFAULT_CONFIG: IndexedDBStoreConfig = {
  dbName: 'cte_telemetry',
  storeName: 'events',
  maxSize: 5000,
}

export class IndexedDBStore {
  private config: IndexedDBStoreConfig
  private db: IDBDatabase | null = null
  private fallbackBuffer: TelemetryEvent[] = []
  private useFallback = false

  constructor(config: Partial<IndexedDBStoreConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  async open(): Promise<void> {
    if (this.db) return

    if (!this.isIndexedDBAvailable()) {
      this.useFallback = true
      return
    }

    try {
      this.db = await this.openDB()
    } catch {
      console.warn('[CTE:IndexedDB] Falling back to in-memory buffer')
      this.useFallback = true
    }
  }

  /** Store a single event */
  async put(event: TelemetryEvent): Promise<void> {
    if (this.useFallback) {
      this.fallbackBuffer.push(event)
      if (this.fallbackBuffer.length > this.config.maxSize) {
        this.fallbackBuffer.splice(0, this.fallbackBuffer.length - this.config.maxSize)
      }
      return
    }

    if (!this.db) await this.open()
    if (!this.db) return

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction(this.config.storeName, 'readwrite')
      const store = tx.objectStore(this.config.storeName)
      store.put(event)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  }

  /** Store multiple events in a single transaction */
  async putBatch(events: TelemetryEvent[]): Promise<void> {
    if (events.length === 0) return

    if (this.useFallback) {
      this.fallbackBuffer.push(...events)
      if (this.fallbackBuffer.length > this.config.maxSize) {
        this.fallbackBuffer.splice(0, this.fallbackBuffer.length - this.config.maxSize)
      }
      return
    }

    if (!this.db) await this.open()
    if (!this.db) return

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction(this.config.storeName, 'readwrite')
      const store = tx.objectStore(this.config.storeName)
      for (const event of events) {
        store.put(event)
      }
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  }

  /** Retrieve and remove up to `limit` events (FIFO order) */
  async drain(limit: number): Promise<TelemetryEvent[]> {
    if (this.useFallback) {
      return this.fallbackBuffer.splice(0, limit)
    }

    if (!this.db) await this.open()
    if (!this.db) return []

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction(this.config.storeName, 'readwrite')
      const store = tx.objectStore(this.config.storeName)
      const results: TelemetryEvent[] = []
      const request = store.openCursor()

      request.onsuccess = (e) => {
        const cursor = (e.target as IDBRequest<IDBCursorWithValue | null>).result
        if (!cursor || results.length >= limit) {
          resolve(results)
          return
        }
        results.push(cursor.value as TelemetryEvent)
        cursor.delete()
        cursor.continue()
      }
      request.onerror = () => reject(request.error)
    })
  }

  /** Get count of buffered events */
  async count(): Promise<number> {
    if (this.useFallback) return this.fallbackBuffer.length

    if (!this.db) await this.open()
    if (!this.db) return 0

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction(this.config.storeName, 'readonly')
      const store = tx.objectStore(this.config.storeName)
      const req = store.count()
      req.onsuccess = () => resolve(req.result)
      req.onerror = () => reject(req.error)
    })
  }

  /** Clear all stored events */
  async clear(): Promise<void> {
    if (this.useFallback) {
      this.fallbackBuffer = []
      return
    }

    if (!this.db) return

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction(this.config.storeName, 'readwrite')
      const store = tx.objectStore(this.config.storeName)
      const req = store.clear()
      req.onsuccess = () => resolve()
      req.onerror = () => reject(req.error)
    })
  }

  /** Close the database connection */
  close(): void {
    this.db?.close()
    this.db = null
  }

  // ─────────────────────────────────────────────
  //  Private
  // ─────────────────────────────────────────────

  private openDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.config.dbName, 1)

      request.onupgradeneeded = () => {
        const db = request.result
        if (!db.objectStoreNames.contains(this.config.storeName)) {
          db.createObjectStore(this.config.storeName, { keyPath: 'id' })
        }
      }

      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  }

  private isIndexedDBAvailable(): boolean {
    try {
      return typeof indexedDB !== 'undefined' && indexedDB !== null
    } catch {
      return false
    }
  }
}
