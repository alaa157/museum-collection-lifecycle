"use client";

import { useEffect, useState } from "react";
import { ClipboardList } from "lucide-react";
import { AuthGuard } from "@/components/auth-guard";
import { domainApi } from "@/lib/domain-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function AuditContent() {
  const [entries, setEntries] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    domainApi.audit
      .list()
      .then(setEntries)
      .catch((err) => {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load audit records."
        );
      });
  }, []);

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <ClipboardList className="h-6 w-6" />
            <h1 className="text-3xl font-semibold">
              Audit history
            </h1>
          </div>

          <p className="mt-2 text-sm text-slate-500">
            Immutable application event history.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent events</CardTitle>
          </CardHeader>

          <CardContent>
            {error ? (
              <p className="text-sm text-red-600">
                {error}
              </p>
            ) : entries.length === 0 ? (
              <p className="text-sm text-slate-500">
                No audit events have been recorded yet.
              </p>
            ) : (
              <div className="divide-y divide-slate-200">
                {entries.map((entry) => (
                  <div key={entry.id} className="py-4">
                    <div className="flex items-center justify-between">
                      <p className="font-medium">
                        {entry.action}
                      </p>

                      <span className="text-xs text-slate-400">
                        {entry.timestamp}
                      </span>
                    </div>

                    <p className="mt-1 text-sm text-slate-600">
                      {entry.entity_type}
                      {entry.entity_id
                        ? ` · ${entry.entity_id}`
                        : ""}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

export default function AuditPage() {
  return (
    <AuthGuard>
      <AuditContent />
    </AuthGuard>
  );
}
