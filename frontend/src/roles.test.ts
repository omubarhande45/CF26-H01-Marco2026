import { describe, expect, it } from "vitest";
import { can, homeFor } from "./roles";

describe("RBAC nav", () => {
  it("researcher can build queries, auditor cannot", () => {
    expect(can("researcher", "query-builder")).toBe(true);
    expect(can("auditor", "query-builder")).toBe(false);
    expect(can("auditor", "audit")).toBe(true);
  });
  it("homes", () => {
    expect(homeFor("auditor")).toBe("/audit");
    expect(homeFor("researcher")).toBe("/dashboard");
  });
});
