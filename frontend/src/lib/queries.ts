/** TanStack Query hooks for candidates. */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchCandidates,
  approveCandidate,
  rejectCandidate,
  type CandidateFilters,
  type CandidateList,
  type Candidate,
} from "./api";

export function useCandidates(filters: CandidateFilters) {
  return useQuery<CandidateList>({
    queryKey: ["candidates", filters],
    queryFn: () => fetchCandidates(filters),
    staleTime: 30_000,
  });
}

export function useApprove() {
  const qc = useQueryClient();

  return useMutation<Candidate, Error, string>({
    mutationFn: (id) => approveCandidate(id),
    onMutate: async (id) => {
      // Optimistic: remove from current list
      await qc.cancelQueries({ queryKey: ["candidates"] });
      qc.setQueriesData<CandidateList>(
        { queryKey: ["candidates"] },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.filter((c) => c.id !== id),
            total: old.total - 1,
          };
        }
      );
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["candidates"] });
    },
  });
}

export function useReject() {
  const qc = useQueryClient();

  return useMutation<Candidate, Error, { id: string; reason?: string }>({
    mutationFn: ({ id, reason }) => rejectCandidate(id, reason),
    onMutate: async ({ id }) => {
      await qc.cancelQueries({ queryKey: ["candidates"] });
      qc.setQueriesData<CandidateList>(
        { queryKey: ["candidates"] },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.filter((c) => c.id !== id),
            total: old.total - 1,
          };
        }
      );
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["candidates"] });
    },
  });
}
