import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ActivityDrawer } from "./ActivityDrawer";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock the icons
vi.mock("@/components/ui/Icon", () => ({
  Icon: ({ name }) => <span>icon-{name}</span>,
}));

// Mock the formatters
vi.mock("@/lib/format", () => ({
  formatCo2e: (v) => `${v} kg CO2e`,
}));

// Mock the query hook
vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useQuery: () => ({
      isLoading: false,
      data: {
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
      },
    }),
    useMutation: () => ({
      isPending: false,
      mutate: vi.fn(),
    }),
  };
});

describe("ActivityDrawer", () => {
  const queryClient = new QueryClient();

  it("renders detail successfully", () => {
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
    expect(screen.getByText("diesel")).toBeInTheDocument();
    expect(screen.getByText("Scope 1")).toBeInTheDocument();
    expect(screen.getAllByText("1,200 L").length).toBe(2);
    expect(screen.getByText("3216 kg CO2e")).toBeInTheDocument();
  });
});
