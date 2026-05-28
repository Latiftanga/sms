<script lang="ts">
  export let id: string;
  export let label: string = "";
  export let value: string = "";
  export let type: string = "text";
  export let placeholder: string = "";
  export let error: string = "";
  export let hint: string = "";
  export let disabled = false;
  export let required = false;
  export let optional = false;
</script>

<div class="field">
  {#if label}
    <label for={id}>
      {label}
      {#if required}<span class="req" aria-hidden="true">*</span>{/if}
      {#if optional}<span class="opt">(optional)</span>{/if}
    </label>
  {/if}
  <input
    {id}
    {type}
    {placeholder}
    {disabled}
    class="input"
    class:invalid={!!error}
    bind:value
    on:input
    on:change
    on:blur
    on:focus
  />
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
    transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
    appearance: none;
    -webkit-appearance: none;
  }
  .input::placeholder { color: var(--tx-placeholder); }

  .input:hover:not(:focus):not(:disabled) {
    border-color: color-mix(in srgb, var(--border-strong) 40%, var(--accent));
    background: var(--surface-1);
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
