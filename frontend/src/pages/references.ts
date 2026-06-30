import { apiGet, apiPost } from "../api/client";
import { showToast } from "../components/toast";
import type { ReferenceGenome } from "../types";

export async function renderReferences(apiBase: string, navigate: (path: string) => void) {
  const title = document.getElementById("page-title")!;
  title.textContent = "Genomas de Referência";

  const content = document.getElementById("page-content")!;

  let refs: ReferenceGenome[] = [];
  try {
    refs = await apiGet<ReferenceGenome[]>(apiBase, "/references");
  } catch {
    // pass
  }

  content.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
      <span style="color:var(--text-secondary); font-size:0.875rem;">
        ${refs.length} referências registradas
      </span>
      <button class="btn btn-primary" id="btn-add-ref">+ Nova Referência</button>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Espécie</th>
            <th>FASTA</th>
            <th>Padrão</th>
            <th>Registrada em</th>
          </tr>
        </thead>
        <tbody>
          ${refs.length === 0
            ? `<tr><td colspan="5"><div class="empty-state"><p>Nenhuma referência registrada</p></div></td></tr>`
            : refs.map(r => `
              <tr>
                <td><strong>${r.name}</strong></td>
                <td>${r.species}</td>
                <td style="font-size:0.8rem; color:var(--text-secondary);">${r.fasta_path}</td>
                <td>${r.is_default ? "✅" : "—"}</td>
                <td>${new Date(r.created_at).toLocaleDateString("pt-BR")}</td>
              </tr>
            `).join("")}
        </tbody>
      </table>
    </div>

    <!-- Add reference form (hidden by default) -->
    <div id="add-ref-form" style="display:none; margin-top:1.5rem;">
      <div class="form-card">
        <h3 style="margin-bottom:1rem;">Registrar Novo Genoma</h3>
        <div class="form-group">
          <label for="ref-name">Nome</label>
          <input type="text" id="ref-name" placeholder="grch38" />
        </div>
        <div class="form-group">
          <label for="ref-fasta">Caminho do FASTA</label>
          <input type="text" id="ref-fasta" placeholder="/ref/grch38/GRCh38.fa" />
        </div>
        <div class="form-group">
          <label for="ref-species">Espécie</label>
          <input type="text" id="ref-species" value="Homo sapiens" />
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" id="ref-default" />
            Referência padrão
          </label>
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" id="btn-save-ref">Registrar</button>
          <button class="btn btn-secondary" id="btn-cancel-ref">Cancelar</button>
        </div>
      </div>
    </div>
  `;

  document.getElementById("btn-add-ref")?.addEventListener("click", () => {
    document.getElementById("add-ref-form")!.style.display = "block";
  });

  document.getElementById("btn-cancel-ref")?.addEventListener("click", () => {
    document.getElementById("add-ref-form")!.style.display = "none";
  });

  document.getElementById("btn-save-ref")?.addEventListener("click", async () => {
    const name = (document.getElementById("ref-name") as HTMLInputElement).value.trim();
    const fasta = (document.getElementById("ref-fasta") as HTMLInputElement).value.trim();
    const species = (document.getElementById("ref-species") as HTMLInputElement).value.trim();
    const isDefault = (document.getElementById("ref-default") as HTMLInputElement).checked;

    if (!name || !fasta) {
      showToast("Preencha nome e caminho do FASTA", "error");
      return;
    }

    try {
      await apiPost(apiBase, "/references", {
        name,
        fasta_path: fasta,
        species,
        is_default: isDefault,
      });
      showToast("Referência registrada com sucesso!", "success");
      navigate("/references");
    } catch (err: unknown) {
      showToast(`Erro: ${err instanceof Error ? err.message : "desconhecido"}`, "error");
    }
  });
}
