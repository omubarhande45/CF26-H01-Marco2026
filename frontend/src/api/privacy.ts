import { api } from "./client";

export function privacyBudget(token: string) {
  return api<{ actor: string; remaining: Record<string, number>; default: number }>("/privacy/budget", token);
}
