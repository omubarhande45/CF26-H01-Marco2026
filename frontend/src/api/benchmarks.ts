import { api } from "./client";

export function getBenchmarks(token: string) {
  return api<{ available: boolean; results: unknown }>("/benchmarks", token);
}
