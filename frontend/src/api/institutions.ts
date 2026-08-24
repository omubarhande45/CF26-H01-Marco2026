import { api } from "./client";

export function listInstitutions(token: string) {
  return api<Array<{ id: string; name: string; url: string; active: boolean }>>("/institutions", token);
}

export function institutionDetail(token: string, id: string) {
  return api<Record<string, unknown>>(`/institutions/${id}`, token);
}
