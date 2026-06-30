import { apiGet, apiPost } from "../api/client";
import { statusBadge } from "../components/badge";
import { showToast } from "../components/toast";
import type { PipelineRun } from "../types";

export async function renderRunDetail(apiBase: string, navigate: (path: string) => void, id: string) {
  const title = document.getElementById("page-title")!;
  const content = document.getElementById("page-content")!;

  let run: PipelineRun;
  try {
    run = await apiGet<PipelineRun>(apiBase, `/runs/${id}`);
  } catch {
    title.textContent = "Execução não encontrada";
    content.innerHTML = `<div class="empty-state"><p>Execução não encontrada</p></div>`;
    return;
  }

  title.textContent = run.name;

  let logsHtml = "";
  try {
    const logsData = await apiGet<{ logs: string }>(apiBase, `/runs/${id}/logs`);
    logsHtml = logsData.logs || "Nenhum log disponível";
  } catch {
    logsHtml = "Logs indisponíveis";
  }

  content.innerHTML = `
    <div class="detail-card">
      <div class="detail-grid">
        <div class="detail-field">
          <div class="label">Status</div>
          <div class="value">${statusBadge(run.status)}</div>
        </div>
        <div class="detail-field">
          <div class="label">Referência</div>
          <div class="value">${run.reference}</div>
        </div>
        <div class="detail-field">
          <div class="label">Samplesheet</div>
          <div class="value">${run.samplesheet_path}</div>
        </div>
        <div class="detail-field">
          <div class="label">Nextflow Run ID</div>
          <div class="value">${run.nextflow_run_id || "—"}</div>
        </div>
        <div class="detail-field">
          <div class="label">Criada em</div>
          <div class="value">${new Date(run.created_at).toLocaleString("pt-BR")}</div>
        </div>
        <div class="detail-field">
          <div class="label">Iniciada em</div>
          <div class="value">${run.started_at ? new Date(run.started_at).toLocaleString("pt-BR") : "—"}</div>
        </div>
        <div class="detail-field">
          <div class="label">Concluída em</div>
          <div class="value">${run.completed_at ? new Date(run.completed_at).toLocaleString("pt-BR") : "—"}</div>
        </div>
        <div class="detail-field">
          <div class="label">Duração</div>
          <div class="value">${run.duration_seconds ? `${run.duration_seconds}s` : "—"}</div>
        </div>
      </div>

      ${run.report_path ? `
        <div style="margin-top:1rem;">
          <a href="${apiBase}/runs/${id}/report" target="_blank" class="btn btn-primary">📊 Ver Relatório MultiQC</a>
        </div>
      ` : ""}

      ${run.error_message ? `
        <div style="margin-top:1rem; padding:0.75rem; background:rgba(239,68,68,0.1); border-radius:6px; color:var(--danger); font-size:0.875rem;">
          <strong>Erro:</strong> ${run.error_message}
        </div>
      ` : ""}

      <div style="margin-top:1rem;">
        <h3 style="font-size:1rem; margin-bottom:0.5rem;">Logs</h3>
        <div class="logs-box">${logsHtml}</div>
      </div>

      <div class="form-actions" style="margin-top:1.5rem;">
        ${run.status === "pending" || run.status === "queued" || run.status === "running"
          ? `<button class="btn btn-danger" id="btn-cancel">Cancelar Execução</button>`
          : ""}
        <button class="btn btn-secondary" id="btn-back">Voltar</button>
      </div>
    </div>
  `;

  document.getElementById("btn-cancel")?.addEventListener("click", async () => {
    if (!confirm("Tem certeza que deseja cancelar esta execução?")) return;
    try {
      await apiPost(apiBase, `/runs/${id}/cancel`, {});
      showToast("Execução cancelada", "success");
      navigate("/");
    } catch (err: unknown) {
      showToast(`Erro: ${err instanceof Error ? err.message : "desconhecido"}`, "error");
    }
  });

  document.getElementById("btn-back")?.addEventListener("click", () => navigate("/"));
}
