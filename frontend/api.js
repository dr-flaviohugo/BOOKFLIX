const API_BASE = localStorage.getItem("bookflix_api_base") || "http://localhost:8000";

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Ignore JSON parsing failure for non-JSON responses.
    }
    throw new Error(detail);
  }
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response;
}

function getSessionId() {
  let id = localStorage.getItem("bookflix_session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("bookflix_session_id", id);
  }
  return id;
}

window.BookflixApi = {
  apiFetch,
  getSessionId,
  API_BASE,
};
