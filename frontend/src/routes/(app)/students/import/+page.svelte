<script lang="ts">
  import { goto } from "$app/navigation";
  import { api } from "$api/client";
  import { toast } from "$stores/toast";
  import Button from "$components/ui/Button.svelte";
  import { ArrowLeft, Upload, Download, Check, AlertCircle, FileText } from "@lucide/svelte";
  import { schoolBranding } from "$stores/school";

  interface BulkUploadResponse {
    created: number;
    skipped: number;
    errors: { row: number; field: string | null; message: string }[];
  }

  let file: File | null = null;
  let uploading = false;
  let result: BulkUploadResponse | null = null;
  let uploadError = "";
  let dragging = false;
  let downloading = false;

  function apiError(e: unknown): string {
    const err = e as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail ?? "Something went wrong.";
  }

  function onFileChange(e: Event) {
    const input = e.target as HTMLInputElement;
    file = input.files?.[0] ?? null;
    result = null; uploadError = "";
  }

  function onDrop(e: DragEvent) {
    e.preventDefault(); dragging = false;
    const dropped = e.dataTransfer?.files?.[0];
    if (dropped && /\.(csv|xlsx|xls)$/i.test(dropped.name)) {
      file = dropped; result = null; uploadError = "";
    }
  }

  async function downloadTemplate() {
    downloading = true;
    try {
      const res = await api.get("/students/bulk/template", { responseType: "blob" });
      const blob = new Blob([res.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const disposition: string = res.headers?.["content-disposition"] ?? "";
      a.download = disposition.match(/filename="?([^"]+)"?/)?.[1] ?? "Student_Import_Template.xlsx";
      a.href = url; a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Could not download template. Try again.");
    } finally {
      downloading = false;
    }
  }

  async function submit() {
    if (!file) return;
    uploading = true; uploadError = ""; result = null;
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post<BulkUploadResponse>("/students/bulk", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      result = data;
      if (data.created > 0) {
        toast.success(`${data.created} student${data.created > 1 ? "s" : ""} imported`);
      }
    } catch (e) {
      uploadError = apiError(e);
    } finally {
      uploading = false;
    }
  }

  function reset() { file = null; result = null; uploadError = ""; }
</script>

<svelte:head><title>Import Students — {$schoolBranding?.name ?? "TTEK SMS"}</title></svelte:head>

<div class="page">
  <button class="back" on:click={() => goto("/students")}>
    <ArrowLeft size={14} /> Students
  </button>

  <div class="header">
    <h1 class="title">Bulk import students</h1>
    <p class="subtitle">Upload a CSV or Excel file to enroll multiple students at once.</p>
  </div>

  <div class="layout">
    <!-- Upload card -->
    <div class="upload-card">
      {#if !result}
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <label
          class="drop-zone"
          class:dragging
          class:has-file={!!file}
          on:dragover|preventDefault={() => dragging = true}
          on:dragleave={() => dragging = false}
          on:drop={onDrop}
        >
          <input type="file" accept=".csv,.xlsx,.xls" on:change={onFileChange} style="display:none" />

          {#if file}
            <div class="file-chosen">
              <FileText size={32} class="file-icon" />
              <div>
                <div class="file-name">{file.name}</div>
                <div class="file-size">{(file.size / 1024).toFixed(1)} KB</div>
              </div>
            </div>
          {:else}
            <Upload size={28} class="drop-icon" />
            <p class="drop-label">Drop your file here, or <span class="browse-link">browse</span></p>
            <p class="drop-hint">Excel (.xlsx) or CSV · max 5 MB</p>
          {/if}
        </label>

        {#if uploadError}
          <div class="error-banner"><AlertCircle size={15} /> {uploadError}</div>
        {/if}

        <div class="upload-actions">
          <Button variant="ghost" loading={downloading} on:click={downloadTemplate}>
            <Download size={13} /> Download template (.xlsx)
          </Button>
          {#if file}<Button variant="ghost" on:click={reset}>Clear</Button>{/if}
          <Button disabled={!file} loading={uploading} on:click={submit}>
            <Upload size={13} /> Import
          </Button>
        </div>

      {:else}
        <!-- Results -->
        <div class="results">
          <div class="result-row ok">
            <Check size={18} />
            <div>
              <strong>{result.created}</strong> student{result.created !== 1 ? "s" : ""} imported successfully
            </div>
          </div>

          {#if result.skipped > 0}
            <div class="result-row muted">
              <span class="dot"></span>
              <div>{result.skipped} blank row{result.skipped !== 1 ? "s" : ""} skipped</div>
            </div>
          {/if}

          {#if result.errors.length > 0}
            <div class="result-row err">
              <AlertCircle size={18} />
              <div><strong>{result.errors.length}</strong> row{result.errors.length !== 1 ? "s" : ""} had errors</div>
            </div>

            <div class="error-table-wrap">
              <table class="error-table">
                <thead><tr><th>Row</th><th>Field</th><th>Problem</th></tr></thead>
                <tbody>
                  {#each result.errors as err}
                    <tr>
                      <td class="row-num">{err.row}</td>
                      <td class="field-name">{err.field ?? "—"}</td>
                      <td class="err-msg">{err.message}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/if}

          <div class="result-actions">
            <Button variant="ghost" on:click={reset}>Import another file</Button>
            <Button on:click={() => goto("/students")}>View students</Button>
          </div>
        </div>
      {/if}
    </div>

    <!-- Instructions sidebar -->
    <aside class="guide">
      <h2 class="guide-title">How it works</h2>

      <ol class="guide-steps">
        <li>
          <span class="step-num">1</span>
          <div>
            <strong>Download the template</strong>
            <p>A branded Excel file with dropdown validations for gender, student type, and guardian relationship, plus two example rows.</p>
          </div>
        </li>
        <li>
          <span class="step-num">2</span>
          <div>
            <strong>Fill in your students</strong>
            <p>Only <em>first_name</em>, <em>last_name</em>, and <em>gender</em> are required. Add <em>class_name</em> to enroll the student — it must match exactly.</p>
          </div>
        </li>
        <li>
          <span class="step-num">3</span>
          <div>
            <strong>Upload and review</strong>
            <p>Rows with errors are listed below. Fix them and re-upload. Students already created won't be duplicated.</p>
          </div>
        </li>
      </ol>

      <div class="guide-note">
        <strong>Required columns</strong>
        <p>first_name · last_name · gender</p>
        <strong>Class enrollment</strong>
        <p>Type the class name exactly as it appears in Settings → Academic Structure (e.g. <code>Basic 4A</code>, <code>2 SCI A</code>).</p>
        <strong>Guardian</strong>
        <p>Fill guardian_first_name, guardian_last_name, guardian_relationship, guardian_phone to create a contact record.</p>
        <strong>Date format</strong>
        <p>YYYY-MM-DD &nbsp;e.g. <code>2012-04-15</code></p>
      </div>
    </aside>
  </div>
</div>

<style>
  .page { display: flex; flex-direction: column; gap: 24px; }

  .back {
    display: inline-flex; align-items: center; gap: 6px;
    background: none; border: none; cursor: pointer;
    color: var(--tx-low); font-size: 0.875rem; padding: 0;
    transition: color 0.12s; width: fit-content;
  }
  .back:hover { color: var(--tx-high); }

  .header { display: flex; flex-direction: column; gap: 4px; }
  .title    { margin: 0; font-size: 1.25rem; font-weight: 700; color: var(--tx-high); }
  .subtitle { margin: 0; font-size: 0.875rem; color: var(--tx-low); }

  .layout { display: grid; grid-template-columns: 1fr 300px; gap: 20px; align-items: start; }
  @media (max-width: 860px) { .layout { grid-template-columns: 1fr; } }

  .upload-card {
    background: var(--surface-0); border: 1px solid var(--border-subtle);
    border-radius: 14px; padding: 24px;
    display: flex; flex-direction: column; gap: 16px;
  }

  .drop-zone {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 10px;
    padding: 48px 24px;
    border: 2px dashed var(--border-subtle); border-radius: 10px;
    cursor: pointer; text-align: center;
    transition: border-color 0.15s, background 0.15s;
  }
  .drop-zone:hover, .drop-zone.dragging {
    border-color: var(--accent);
    background: color-mix(in srgb, var(--accent) 4%, transparent);
  }
  .drop-zone.has-file {
    border-color: var(--ok-dot, #10b981);
    background: color-mix(in srgb, var(--ok-dot, #10b981) 5%, transparent);
    padding: 32px 24px;
  }
  .drop-zone :global(.drop-icon) { color: var(--tx-low); }
  .drop-zone :global(.file-icon) { color: var(--ok-dot, #10b981); }
  .drop-label { margin: 0; font-size: 0.9rem; color: var(--tx-mid); }
  .browse-link { color: var(--accent); text-decoration: underline; }
  .drop-hint { margin: 0; font-size: 0.8rem; color: var(--tx-low); }
  .file-chosen { display: flex; align-items: center; gap: 14px; text-align: left; }
  .file-name { font-size: 0.9375rem; font-weight: 600; color: var(--tx-high); }
  .file-size { font-size: 0.8rem; color: var(--tx-low); margin-top: 2px; }

  .error-banner {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 14px; border-radius: 8px; font-size: 0.875rem;
    color: #ef4444;
    background: color-mix(in srgb, #ef4444 8%, transparent);
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
  }

  .upload-actions { display: flex; gap: 8px; justify-content: flex-end; }

  .results { display: flex; flex-direction: column; gap: 14px; }
  .result-row {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 12px 16px; border-radius: 10px; font-size: 0.9rem;
  }
  .result-row.ok {
    background: color-mix(in srgb, #10b981 8%, transparent); color: #059669;
    border: 1px solid color-mix(in srgb, #10b981 25%, transparent);
  }
  .result-row.muted {
    background: var(--surface-1); color: var(--tx-low);
    border: 1px solid var(--border-subtle);
  }
  .result-row.err {
    background: color-mix(in srgb, #ef4444 8%, transparent); color: #dc2626;
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
  }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--tx-low); margin-top: 5px; flex-shrink: 0;
  }

  .error-table-wrap {
    border: 1px solid var(--border-subtle); border-radius: 8px;
    overflow: hidden; max-height: 280px; overflow-y: auto;
  }
  .error-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
  .error-table th {
    text-align: left; padding: 8px 12px;
    font-size: 0.7rem; font-weight: 600; color: var(--tx-low);
    text-transform: uppercase; letter-spacing: 0.05em;
    background: var(--surface-1); border-bottom: 1px solid var(--border-subtle);
  }
  .error-table td {
    padding: 9px 12px;
    border-bottom: 1px solid color-mix(in srgb, var(--border-subtle) 50%, transparent);
    vertical-align: top;
  }
  .error-table tr:last-child td { border-bottom: none; }
  .row-num    { font-weight: 700; color: var(--tx-high); width: 48px; }
  .field-name { font-family: monospace; color: var(--err-text, #dc2626); white-space: nowrap; }
  .err-msg    { color: var(--tx-mid); }
  .result-actions { display: flex; gap: 8px; justify-content: flex-end; padding-top: 4px; }

  .guide {
    background: var(--surface-0); border: 1px solid var(--border-subtle);
    border-radius: 14px; padding: 22px;
    display: flex; flex-direction: column; gap: 18px;
  }
  .guide-title { margin: 0; font-size: 0.9375rem; font-weight: 700; color: var(--tx-high); }
  .guide-steps { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 16px; }
  .guide-steps li { display: flex; gap: 12px; align-items: flex-start; }
  .step-num {
    width: 22px; height: 22px; border-radius: 50%;
    background: color-mix(in srgb, var(--accent) 12%, transparent);
    color: var(--accent); font-size: 0.75rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
  }
  .guide-steps strong { font-size: 0.875rem; color: var(--tx-high); display: block; margin-bottom: 2px; }
  .guide-steps p { margin: 0; font-size: 0.8125rem; color: var(--tx-low); line-height: 1.5; }
  .guide-note {
    padding: 14px; border-radius: 8px;
    background: var(--surface-1); border: 1px solid var(--border-subtle);
    display: flex; flex-direction: column; gap: 4px;
  }
  .guide-note strong { font-size: 0.75rem; font-weight: 600; color: var(--tx-mid); text-transform: uppercase; letter-spacing: 0.05em; }
  .guide-note p { margin: 0 0 8px; font-size: 0.8125rem; color: var(--tx-low); }
  .guide-note code {
    font-family: monospace; font-size: 0.8rem;
    background: var(--surface-0); padding: 1px 5px; border-radius: 4px;
    border: 1px solid var(--border-subtle);
  }
</style>
