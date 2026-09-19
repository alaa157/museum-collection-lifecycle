"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import {
  Archive,
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
  SlidersHorizontal
} from "lucide-react";

import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent
} from "@/components/ui/card";
import { domainApi, CollectionItem } from "@/lib/domain-api";

function CollectionContent() {
  const [items, setItems] = useState<CollectionItem[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const limit = 20;

  async function loadItems(
    nextOffset = offset,
    nextQuery = query,
    nextStatus = status
  ) {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();

      if (nextQuery.trim()) {
        params.set(
          "search",
          nextQuery.trim()
        );
      }

      if (nextStatus) {
        params.set("status", nextStatus);
      }

      params.set(
        "offset",
        String(nextOffset)
      );

      params.set(
        "limit",
        String(limit)
      );

      const result =
        await domainApi.collection.list(
          params
        );

      setItems(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load collection."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadItems(0, "", "");
  }, []);

  function submitSearch(
    event: FormEvent
  ) {
    event.preventDefault();

    setOffset(0);
    setQuery(search);

    loadItems(
      0,
      search,
      status
    );
  }

  function changeStatus(
    value: string
  ) {
    setStatus(value);
    setOffset(0);

    loadItems(
      0,
      query,
      value
    );
  }

  const canPrevious = offset > 0;
  const canNext =
    offset + limit < total;

  return (
    <div className="p-5 lg:p-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <Archive className="h-6 w-6" />
              <h1 className="text-3xl font-semibold">
                Collection
              </h1>
            </div>

            <p className="mt-2 text-sm text-slate-500">
              Search, filter and open institutional collection records.
            </p>
          </div>

          <Link href="/collection/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Register object
            </Button>
          </Link>
        </div>

        <Card>
          <CardContent className="p-5">
            <form
              onSubmit={submitSearch}
              className="grid gap-3 md:grid-cols-[1fr_210px_auto]"
            >
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-5 w-5 text-slate-400" />

                <Input
                  className="pl-10"
                  placeholder="Accession, object number, title"
                  value={search}
                  onChange={(event) =>
                    setSearch(
                      event.target.value
                    )
                  }
                />
              </div>

              <div className="relative">
                <SlidersHorizontal className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />

                <select
                  className="h-10 w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 text-sm"
                  value={status}
                  onChange={(event) =>
                    changeStatus(
                      event.target.value
                    )
                  }
                >
                  <option value="">
                    All statuses
                  </option>
                  <option value="ACTIVE">
                    Active
                  </option>
                  <option value="ON_DISPLAY">
                    On display
                  </option>
                  <option value="IN_STORAGE">
                    In storage
                  </option>
                  <option value="ON_LOAN">
                    On loan
                  </option>
                  <option value="UNDER_CONSERVATION">
                    Under conservation
                  </option>
                  <option value="MISSING">
                    Missing
                  </option>
                  <option value="DEACCESSIONED">
                    Deaccessioned
                  </option>
                </select>
              </div>

              <Button type="submit">
                Search
              </Button>
            </form>
          </CardContent>
        </Card>

        {error && (
          <Card className="mt-5">
            <CardContent className="p-5 text-sm text-red-600">
              {error}
            </CardContent>
          </Card>
        )}

        <Card className="mt-5">
          <CardContent className="p-0">
            {loading ? (
              <div className="p-10 text-center text-sm text-slate-500">
                Loading collection…
              </div>
            ) : items.length === 0 ? (
              <div className="p-10 text-center">
                <p className="font-medium">
                  No collection records found
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  Try changing your search or filters.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-200">
                {items.map((item) => (
                  <Link
                    key={item.id}
                    href={`/collection/${item.id}`}
                    className="block p-5 transition hover:bg-slate-50"
                  >
                    <div className="flex items-center justify-between gap-6">
                      <div className="min-w-0">
                        <p className="truncate font-semibold">
                          {item.title}
                        </p>

                        <p className="mt-1 text-sm text-slate-500">
                          {item.accession_number}
                          {" · "}
                          {item.object_number}
                        </p>
                      </div>

                      <span className="shrink-0 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium">
                        {item.status.replaceAll(
                          "_",
                          " "
                        )}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}

            <div className="flex items-center justify-between border-t border-slate-200 px-5 py-4">
              <p className="text-sm text-slate-500">
                {total === 0
                  ? "0 records"
                  : `${offset + 1}–${Math.min(
                      offset + limit,
                      total
                    )} of ${total}`}
              </p>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!canPrevious}
                  onClick={() => {
                    const nextOffset =
                      Math.max(
                        0,
                        offset - limit
                      );

                    setOffset(
                      nextOffset
                    );

                    loadItems(
                      nextOffset
                    );
                  }}
                >
                  <ChevronLeft className="mr-1 h-4 w-4" />
                  Previous
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  disabled={!canNext}
                  onClick={() => {
                    const nextOffset =
                      offset + limit;

                    setOffset(
                      nextOffset
                    );

                    loadItems(
                      nextOffset
                    );
                  }}
                >
                  Next
                  <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function CollectionPage() {
  return (
    <AuthGuard>
      <AppShell>
        <CollectionContent />
      </AppShell>
    </AuthGuard>
  );
}
