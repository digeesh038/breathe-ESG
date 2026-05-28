import { describe, expect, it } from "vitest";
import { formatCo2e, formatCo2eParts } from "./format";

describe("formatCo2e", () => {
  it("converts kg to tonnes with the CO2e unit", () => {
    expect(formatCo2e(52650.986)).toBe("52.65 t CO₂e");
  });

  it("returns an em dash for null", () => {
    expect(formatCo2e(null)).toBe("—");
  });

  it("rounds to two decimals", () => {
    expect(formatCo2e(1234)).toBe("1.23 t CO₂e");
  });
});

describe("formatCo2eParts", () => {
  it("splits value and unit", () => {
    expect(formatCo2eParts(52650.986)).toEqual({ value: "52.65", unit: "t CO₂e" });
  });

  it("handles null", () => {
    expect(formatCo2eParts(null)).toEqual({ value: "—", unit: "" });
  });
});
