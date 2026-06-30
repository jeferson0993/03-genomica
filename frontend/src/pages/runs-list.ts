import { apiGet } from "../api/client";
import { statusBadge } from "../components/badge";
import type { PipelineRun } from "../types";

export async function renderRunsList(apiBase: string, navigate: (path: string) => void) {
  const title = document.getElementById("page-title")!;
  title.textContent = "Execuções";

  const content = document.getElementById("page-content")!;

  let runs: PipelineRun[] = [];
  try {
    const data = await apiGet<{ items: PipelineRun[]; total: number }>(apiBase, "/runs");
    runs = data.items;
  } catch {
    // pass
  }

  content.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
      <span style="color:var(--text-secondary); font-size:0.875rem;">
        ${runs.length} execuções
      </span>
      <button class="btn btn-primary" id="btn-new-run">+ Nova Execução</button>
    </div>
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Status</th>
            <th>Referência</th>
            <th>Criada em</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${runs.length === 0
            ? `<tr><td colspan="5"><div class="empty-state"><p>Nenhuma execução encontrada</p></div></td></tr>`
            : runs.map(r => `
              <tr>
                <td><strong>${r.name}</strong></td>
                <td>${statusBadge(r.status)}</td>
                <td>${r.reference}</td>
                <td>${new Date(r.created_at).toLocaleString("pt-BR")}</td>
                <td><a href="/genomics/runs/${r.id}" class="btn btn-secondary" style="padding:0.25rem 0.75rem;">Detalhes</a></td>
              </tr>
            `).join("")}
        </tbody>
      </table>
    </div>
  `;

  document.getElementById("btn-new-run")?.addEventListener("click", () => {
    navigate("/runs/new");
  });

  content.querySelectorAll('a[href^="/genomics/runs/"]').forEach(el => {
    el.addEventListener("click", e => {
      e.preventDefault();
      navigate(el.getAttribute("href")!.replace("/genomics", ""));
    });
  });
}
