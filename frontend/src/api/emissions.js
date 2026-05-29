import { apiClient, unwrap } from "./client";

export const emissionsApi = {
  listActivities: (params) =>
    apiClient.get("/emissions/activities/", { params }).then(unwrap),

  // Dashboard figures, computed server-side (excludes rejected records).
  summary: () =>
    apiClient.get("/emissions/activities/summary/").then((r) => r.data),

  // Detail view includes source history (the raw record).
  getActivity: (id) =>
    apiClient.get(`/emissions/activities/${id}/`).then((r) => r.data),

  updateActivity: (id, patch) =>
    apiClient.patch(`/emissions/activities/${id}/`, patch).then((r) => r.data),

  deleteActivity: (id) => apiClient.delete(`/emissions/activities/${id}/`),

  // Streams CSV or XLSX bytes for download. Filters apply via querystring.
  // NB: the param is `fmt`, not `format` — `format` is reserved by DRF for
  // content negotiation and would 404 before the export view runs.
  exportActivities: (format = "csv", params = {}) =>
    apiClient
      .get("/emissions/act_xport/", {
        params: { fmt: format, ...params },
        responseType: "blob",
      })
      .then((r) => r.data),
};
