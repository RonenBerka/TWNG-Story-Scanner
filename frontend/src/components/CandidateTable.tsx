import { useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from "@tanstack/react-table";
import type { Candidate } from "../lib/api";

interface Props {
  data: Candidate[];
  onRowClick: (candidate: Candidate) => void;
  selectedId?: string;
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function fmtScore(score: number | null): string {
  if (score == null) return "—";
  return score.toFixed(2);
}

export default function CandidateTable({ data, onRowClick, selectedId }: Props) {
  const columns = useMemo<ColumnDef<Candidate>[]>(
    () => [
      {
        accessorKey: "story_score",
        header: "Score",
        cell: (info) => fmtScore(info.getValue<number | null>()),
        size: 70,
      },
      {
        accessorKey: "source_type",
        header: "Source",
        size: 80,
      },
      {
        accessorKey: "created_at_source",
        header: "Date",
        cell: (info) => fmtDate(info.getValue<string | null>()),
        size: 110,
      },
      {
        accessorKey: "category_pred",
        header: "Category",
        cell: (info) => info.getValue<string | null>() || "—",
        size: 120,
      },
      {
        accessorKey: "language",
        header: "Lang",
        size: 55,
      },
      {
        accessorKey: "title",
        header: "Title",
        cell: (info) => {
          const title = info.getValue<string | null>() || "—";
          return title.length > 80 ? title.slice(0, 77) + "..." : title;
        },
      },
      {
        accessorKey: "status",
        header: "Status",
        size: 80,
      },
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => (
                <th key={header.id} style={{ width: header.getSize() }}>
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={{ textAlign: "center", padding: "2rem", color: "#888" }}>
                No candidates found
              </td>
            </tr>
          ) : (
            table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => onRowClick(row.original)}
                className={row.original.id === selectedId ? "selected" : ""}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
