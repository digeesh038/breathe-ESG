import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { ActivityDrawer } from "./ActivityDrawer";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { emissionsApi } from "@/api/emissions";

// Mock the icons
vi.mock("@/components/ui/Icon", () => ({
  Icon: ({ name }) => <span>icon-{name}</span>,
}));

// Mock the formatters
vi.mock("@/lib/format", () => ({
  formatCo2e: (v) => `${v} kg CO2e`,
  formatCo2eParts: (v) => ({ value: String(v), unit: "kg CO2e" }),
}));

// Mock emissionsApi
vi.mock("@/api/emissions", () => ({
  emissionsApi: {
    getActivity: vi.fn(),
    updateActivity: vi.fn(),
  },
}));

describe("ActivityDrawer Integration with real react-query", () => {
  it("renders detail successfully using real react-query", async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    vi.mocked(emissionsApi.getActivity).mockResolvedValue({
      id: 1,
      activity_category: "diesel",
      scope: "1",
      site_code: "Chennai",
      activity_date: "2025-05-12",
      original_quantity: 1200,
      quantity: 1200,
      unit: "L",
      co2e_kg: 3216,
      is_edited: false,
      factor: {
        co2e_per_unit: 2.68,
        unit: "L",
        source: "DEFRA",
      },
      raw: {
        row_number: 1,
        status: "normalized",
        payload: { Plant: "Chennai", Fuel: "Diesel", Menge: "1200" },
        batch: {
          source_type: "sap",
          filename: "sap.csv",
          received_at: "2026-05-28T22:00:00Z",
        },
      },
    });

    const item = {
      id: 1,
      activity: 1,
      status: "pending",
      flags: [],
    };

    render(
      <QueryClientProvider client={queryClient}>
        <ActivityDrawer item={item} onClose={vi.fn()} />
      </QueryClientProvider>,
    );

    // Should display loading first
    expect(screen.getByText("Loading…")).toBeInTheDocument();

    // Wait for the query to resolve and verify layout
    await waitFor(() => {
      expect(screen.queryByText("Loading…")).not.toBeInTheDocument();
    });

    expect(screen.getByText("diesel")).toBeInTheDocument();
    expect(screen.getByText("Scope 1")).toBeInTheDocument();
    expect(screen.getAllByText(/1,200/)[0]).toBeInTheDocument();
  });
});
