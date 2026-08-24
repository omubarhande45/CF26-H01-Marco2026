import { api } from "./client";

export type Disease = {
  disease_id: string;
  disease_name: string;
  disease_category: string;
  icd10_code: string;
};

export type CatalogInstitution = {
  institution_id: string;
  institution_name: string;
  institution_type: string;
  location: string;
  node_id: string | null;
};

export function catalogDiseases(token: string) {
  return api<Disease[]>("/catalog/diseases", token);
}

export function catalogInstitutions(token: string) {
  return api<CatalogInstitution[]>("/catalog/institutions", token);
}

export function catalogYears(token: string) {
  return api<{ years: number[] }>("/catalog/years", token);
}
