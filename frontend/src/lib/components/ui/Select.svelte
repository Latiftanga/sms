<script lang="ts">
  export let id: string;
  export let label: string = "";
  export let value: string = "";
  export let error: string = "";
  export let hint: string = "";
  export let disabled = false;
  export let required = false;
  export let optional = false;
  export let placeholder: string = "";

  /** Convenience prop: pass flat array of strings or {value, label} objects */
  export let options: string[] | { value: string; label: string }[] = [];

  function isObj(o: unknown): o is { value: string; label: string } {
    return typeof o === "object" && o !== null && "value" in o;
  }
</script>

<div class="field">
  {#if label}
    <label for={id}>
      {label}
      {#if required}<span class="req" aria-hidden="true">*</span>{/if}
      {#if optional}<span class="opt">(optional)</span>{/if}
    </label>
  {/if}
  <select
    {id}
    {disabled}
    class="input"
    class:invalid={!!error}
    bind:value
    on:change
    on:blur
  >
    {#if placeholder}
      <option value="">{placeholder}</option>
    {/if}
    <!-- Pass options prop OR use a slot for custom <option> elements -->
    {#each options as opt}
      {#if isObj(opt)}
        <option value={opt.value}>{opt.label}</option>
      {:else}
        <option value={opt}>{opt}</option>
      {/if}
    {/each}
    <slot />
  </select>
  {#if error}<p class="ferr" role="alert">{error}</p>{/if}
  {#if hint && !error}<p class="hint">{hint}</p>{/if}
</div>

<style>
  .field { display: flex; flex-direction: column; gap: 5px; }

  label {
    font-size: 12px;
    font-weight: 600;
    color: var(--tx-mid);
    letter-spacing: 0.01em;
    user-select: none;
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .req  { color: var(--accent); }
  .opt  { font-weight: 400; font-size: 11px; color: var(--tx-low); }

  .input {
    width: 100%;
    height: 34px;
    padding: 0 11px;
    border: 1px solid var(--border-strong);
    border-radius: 6px;
    background: var(--surface-0);
    color: var(--tx-high);
    font-size: 13px;
    font-family: inherit;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
    appearance: none;
    -webkit-appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2396938B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
    padding-right: 30px;
    cursor: pointer;
  }

  .input:hover:not(:focus):not(:disabled) {
    border-color: color-mix(in srgb, var(--border-strong) 40%, var(--accent));
  }

  .input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 13%, transparent);
  }

  .input.invalid { border-color: var(--err-text); }
  .input.invalid:focus { box-shadow: 0 0 0 3px color-mix(in srgb, var(--err-text) 12%, transparent); }

  .input:disabled { opacity: 0.55; cursor: not-allowed; }

  .ferr { font-size: 11.5px; color: var(--err-text); margin: 0; }
  .hint { font-size: 11.5px; color: var(--tx-low); margin: 0; }
</style>
