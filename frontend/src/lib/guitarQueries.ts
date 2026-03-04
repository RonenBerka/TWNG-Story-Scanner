import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchAllGuitars,
  approveGuitar,
  rejectGuitar,
  insertExtractedGuitar,
  sendClaimEmail,
} from "./guitars";
import type { Guitar } from "../types/guitar";

export function useGuitars(status?: string) {
  return useQuery<Guitar[]>({
    queryKey: ["guitars", status || "all"],
    queryFn: () => fetchAllGuitars(status),
    staleTime: 15_000,
  });
}

export function useApproveGuitar() {
  const qc = useQueryClient();

  return useMutation<string, Error, string>({
    mutationFn: (id) => approveGuitar(id),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["guitars"] });
    },
  });
}

export function useRejectGuitar() {
  const qc = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (id) => rejectGuitar(id),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["guitars"] });
    },
  });
}

export function useInsertExtraction() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: insertExtractedGuitar,
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["guitars"] });
    },
  });
}

export function useSendClaimEmail() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: sendClaimEmail,
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["guitars"] });
    },
  });
}
