import { apiClient, unwrap } from "./client";

export const ingestionApi = {
  listSources: () => apiClient.get("/ingestion/sources/").then(unwrap),

  listBatches: () => apiClient.get("/ingestion/batches/").then(unwrap),

  upload: (sourceId, file) => {
    const form = new FormData();
    form.append("source", String(sourceId));
    form.append("file", file);
    return apiClient.post("/ingestion/batches/upload/", form).then((r) => r.data);
  },

  rawRecords: (batchId) =>
    apiClient
      .get("/ingestion/raw-records/", { params: { batch: batchId } })
      .then(unwrap),
};
