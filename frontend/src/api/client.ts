export async function apiGet<T>(base: string, path: string): Promise<T> {
  const res = await fetch(`${base}${path}`);
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`GET ${path} ${res.status}: ${err}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T>(base: string, path: string, body: unknown): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`POST ${path} ${res.status}: ${err}`);
  }
  return res.json() as Promise<T>;
}
