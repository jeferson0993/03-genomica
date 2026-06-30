import { renderRunsList, renderRunCreate, renderRunDetail, renderReferences } from "./pages/index";
import "./style.css";

const API_BASE = "/api/genomics";

function navigate(path: string) {
  history.pushState(null, "", path);
  render();
}

function render() {
  const path = location.pathname.replace(/^\/genomics/, "") || "/";

  if (path === "/") {
    renderRunsList(API_BASE, navigate);
  } else if (path === "/runs/new") {
    renderRunCreate(API_BASE, navigate);
  } else if (path.match(/^\/runs\/(.+)$/)) {
    const id = path.match(/^\/runs\/(.+)$/)![1];
    renderRunDetail(API_BASE, navigate, id);
  } else if (path === "/references") {
    renderReferences(API_BASE, navigate);
  }
}

window.addEventListener("popstate", render);
document.addEventListener("DOMContentLoaded", render);
