/**
 * Generic type-safe event emitter.
 *
 * Reusable base class for all CTE subsystems that need pub/sub.
 * Implements the IEmitter<T> interface from types.ts.
 *
 * Design:
 *   - Zero dependencies
 *   - O(1) emit via Set iteration
 *   - Unsubscribe returns a disposer function (React-friendly)
 *   - Supports `once` for one-shot listeners
 */

import type { IEmitter } from '../types'

export class Emitter<TEventMap extends Record<string, any>> implements IEmitter<TEventMap> {
  private listeners = new Map<keyof TEventMap, Set<(data: never) => void>>()

  on<K extends keyof TEventMap>(event: K, handler: (data: TEventMap[K]) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(handler as (data: never) => void)

    // Return disposer
    return () => this.off(event, handler)
  }

  once<K extends keyof TEventMap>(event: K, handler: (data: TEventMap[K]) => void): () => void {
    const wrapper = (data: TEventMap[K]) => {
      this.off(event, wrapper)
      handler(data)
    }
    return this.on(event, wrapper)
  }

  off<K extends keyof TEventMap>(event: K, handler: (data: TEventMap[K]) => void): void {
    this.listeners.get(event)?.delete(handler as (data: never) => void)
  }

  emit<K extends keyof TEventMap>(event: K, data: TEventMap[K]): void {
    const handlers = this.listeners.get(event)
    if (!handlers) return
    handlers.forEach((handler) => {
      try {
        ;(handler as (data: TEventMap[K]) => void)(data)
      } catch (err) {
        console.error(`[CTE Emitter] Error in "${String(event)}" handler:`, err)
      }
    })
  }

  /** Remove all listeners for all events. Call on destroy. */
  removeAllListeners(): void {
    this.listeners.clear()
  }

  /** Remove all listeners for a specific event. */
  removeListenersFor<K extends keyof TEventMap>(event: K): void {
    this.listeners.delete(event)
  }

  /** Get listener count for debugging. */
  listenerCount<K extends keyof TEventMap>(event: K): number {
    return this.listeners.get(event)?.size ?? 0
  }
}
