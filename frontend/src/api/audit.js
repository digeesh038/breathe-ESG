import { apiClient, unwrap } from "./client";

export const auditApi = {
  list: (params) => apiClient.get("/audit/events/", { params }).then(unwrap),
};
