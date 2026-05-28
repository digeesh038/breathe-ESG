import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reviewApi } from "@/api/review";

// Encapsulates the review-queue data + approve/reject mutations so the page
// component stays declarative. Invalidates the list and the dashboard summary
// on every sign-off action.
export function useReviewItems(status) {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["review-items"] });
    qc.invalidateQueries({ queryKey: ["summary"] });
  };

  const query = useQuery({
    queryKey: ["review-items", status],
    queryFn: () => reviewApi.list(status),
  });

  const approve = useMutation({
    mutationFn: (vars) => reviewApi.approve(vars.id, vars.comment),
    onSuccess: invalidate,
  });

  const reject = useMutation({
    mutationFn: (vars) => reviewApi.reject(vars.id, vars.comment),
    onSuccess: invalidate,
  });

  return { ...query, approve, reject };
}
