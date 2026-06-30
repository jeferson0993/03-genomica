import { apiGet, apiPost } from "../api/client";
import { showToast } from "../components/toast";
import type { ReferenceGenome } from "../types";

export async function renderRunCreate(apiBase: string, navigate: (path: string) => void) {
  const title = document.getElementById("page-title")!;
  title.textContent = "Nova Execução";

  const content = document.getElementById("page-content")!;

  let refs: ReferenceGenome[] = [];
  try {
    const data = await apiGet<ReferenceGenome[]>(apiBase, "/references");
    refs = data;
  } catch {
    // pass
  }

  content.innerHTML = `
    <div class="form-card">
      <div class="form-group">
        <label for="run-name">Nome da Execução</label>
        <input type="text" id="run-name" placeholder="ex: cohort-01" />
      </div>
      <div class="form-group">
        <label for="samplesheet">Caminho da Samplesheet</label>
        <input type="text" id="samplesheet" placeholder="raw://genomics/samplesheets/cohort.csv" />
      </div>
      <div class="form-group">
        <label for="reference">Genoma de Referência</label>
        <select id="reference">
          ${refs.length === 0
            ? '<option value="grch38">grch38</option>'
            : refs.map(r =>
                `<option value="${r.name}" ${r.is_default ? "selected" : ""}>${r.name}</option>`
              ).join("")
          }
        </select>
      </div>
      <div class="form-group">
        <label for="params-extra">Parâmetros Extras (JSON opcional)</label>
        <textarea id="params-extra" rows="3" placeholder='{"some_extra_param": "value"}'></textarea>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" id="btn-submit">Disparar Pipeline</button>
        <button class="btn btn-secondary" id="btn-cancel">Cancelar</button>
      </div>
    </div>
  `;

  document.getElementById("btn-submit")?.addEventListener("click", async () => {
    const name = (document.getElementById("run-name") as HTMLInputElement).value.trim();
    const samplesheet = (document.getElementById("samplesheet") as HTMLInputElement).value.trim();
    const ref = (document.getElementById("reference") as HTMLSelectElement).value;

    if (!name || !samplesheet) {
      showToast("Preencha nome e caminho da samplesheet", "error");
      return;
    }

    let params: Record<string, unknown> | undefined;
    const paramsRaw = (document.getElementById("params-extra") as HTMLTextAreaElement).value.trim();
    if (paramsRaw) {
      try {
        params = JSON.parse(paramsRaw);
      } catch {
        showToast("Parâmetros JSON inválidos", "error");
        return;
      }
    }

    try {
      await apiPost(apiBase, "/runs", {
        name,
        samplesheet_path: samplesheet,
        reference: ref,
        params,
      });
      showToast("Pipeline disparada com sucesso!", "success");
      navigate("/");
    } catch (err: unknown) {
      showToast(`Erro: ${err instanceof Error ? err.message : "desconhecido"}`, "error");
    }
  });

  document.getElementById("btn-cancel")?.addEventListener("click", () => navigate("/"));
}
