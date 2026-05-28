import { apiClient, unwrap } from "./client";

export const reviewApi = {
  list: (status) =>
    apiClient
      .get("/review/items/", { params: status ? { status } : {} })
      .then(unwrap),

  approve: (id, comment) =>
    apiClient.post(`/review/items/${id}/approve/`, { comment }).then((r) => r.data),

  reject: (id, comment) =>
    apiClient.post(`/review/items/${id}/reject/`, { comment }).then((r) => r.data),
};
