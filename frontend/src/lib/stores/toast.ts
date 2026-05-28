import { writable } from "svelte/store";

export type ToastVariant = "success" | "error" | "warning" | "info";

export interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
  duration: number;
}

function createToastStore() {
  const { subscribe, update } = writable<ToastItem[]>([]);

  function add(message: string, variant: ToastVariant, duration = 4000) {
    const id = Math.random().toString(36).slice(2, 9);
    update((items) => [...items, { id, message, variant, duration }]);
    if (duration > 0) setTimeout(() => remove(id), duration);
    return id;
  }

  function remove(id: string) {
    update((items) => items.filter((t) => t.id !== id));
  }

  return {
    subscribe,
    success: (msg: string, duration?: number) => add(msg, "success", duration),
    error:   (msg: string, duration?: number) => add(msg, "error", duration),
    warning: (msg: string, duration?: number) => add(msg, "warning", duration),
    info:    (msg: string, duration?: number) => add(msg, "info", duration),
    remove,
  };
}

export const toast = createToastStore();
