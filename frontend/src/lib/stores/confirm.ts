import { writable } from "svelte/store";

export interface ConfirmOptions {
  title: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "default" | "danger";
}

interface ConfirmState {
  open: boolean;
  options: ConfirmOptions;
  loading: boolean;
  resolve: ((value: boolean) => void) | null;
}

function createConfirmStore() {
  const { subscribe, set, update } = writable<ConfirmState>({
    open: false,
    options: { title: "" },
    loading: false,
    resolve: null,
  });

  function show(options: ConfirmOptions): Promise<boolean> {
    return new Promise((resolve) => {
      set({ open: true, options, loading: false, resolve });
    });
  }

  function respond(value: boolean) {
    update((s) => {
      s.resolve?.(value);
      return { ...s, open: false, loading: false, resolve: null };
    });
  }

  function setLoading(value: boolean) {
    update((s) => ({ ...s, loading: value }));
  }

  return { subscribe, show, respond, setLoading };
}

export const confirmDialog = createConfirmStore();
