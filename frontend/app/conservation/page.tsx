"use client";

import { useEffect, useState } from "react";
import {
  Beaker,
  ClipboardCheck,
  Thermometer
} from "lucide-react";
import { AuthGuard } from "@/components/auth-guard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { domainApi, ConditionReport, Treatment } from "@/lib/domain-api";
import { useCurrentUser } from "@/components/auth-guard";
import { can } from "@/lib/permissions";

function ConservationContent() {
  const [itemId, setItemId] = useState("");
  const [reports, setReports] = useState<ConditionReport[]>([]);
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [error, setError] = useState("");

  const user = useCurrentUser();

  async function load() {
    setError("");

    if (!itemId.trim()) {
      setError("Enter a collection item ID.");
      return;
    }

    try {
      const [nextReports, nextTreatments] = await Promise.all([
        domainApi.conservation.conditionReports(itemId),
        domainApi.conservation.treatments(itemId)
      ]);

      setReports(nextReports);
      setTreatments(nextTreatments);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load records.");
    }
  }

  useEffect(() => {
    // Deliberately no fake/default item.
  }, []);

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <Beaker className="h-6 w-6" />
            <h1 className="text-3xl font-semibold">Conservation</h1>
          </div>

          <p className="mt-2 text-sm text-slate-500">
            Condition reporting, treatment workflows and environmental review.
          </p>
        </div>

        <Card>
          <CardContent className="p-6">
            <div className="flex gap-3">
              <input
                className="flex h-10 flex-1 rounded-lg border border-slate-300 bg-white px-3 text-sm"
                placeholder="Collection item UUID"
                value={itemId}
                onChange={(event) => setItemId(event.target.value)}
              />
              {can(user, "conservation:read") && (
                <button
                  className="rounded-lg bg-slate-900 px-5 text-sm font-medium text-white"
                  onClick={load}
                >
                  Load
                </button>
              )}
            </div>

            {error && (
              <p className="mt-3 text-sm text-red-600">
                {error}
              </p>
            )}
          </CardContent>
        </Card>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ClipboardCheck className="h-5 w-5" />
                Condition reports
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-3">
              {reports.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No condition reports loaded.
                </p>
              ) : (
                reports.map((report) => (
                  <div
                    key={report.id}
                    className="rounded-lg border border-slate-200 p-4"
                  >
                    <div className="flex justify-between">
                      <span className="font-medium">
                        Score {report.condition_score}
                      </span>
                      <span className="text-xs text-slate-500">
                        {report.report_date}
                      </span>
                    </div>

                    <p className="mt-2 text-sm text-slate-600">
                      {report.observed_damage || "No observed damage notes."}
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Beaker className="h-5 w-5" />
                Treatments
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-3">
              {treatments.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No treatments loaded.
                </p>
              ) : (
                treatments.map((treatment) => (
                  <div
                    key={treatment.id}
                    className="rounded-lg border border-slate-200 p-4"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">
                        {treatment.treatment_type}
                      </span>

                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs">
                        {treatment.status}
                      </span>
                    </div>

                    <p className="mt-2 text-sm text-slate-500">
                      {treatment.start_date || "Not started"}
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Thermometer className="h-5 w-5" />
              Environmental monitoring
            </CardTitle>
          </CardHeader>

          <CardContent>
            <p className="text-sm text-slate-500">
              Environmental observations are available through the conservation
              API and will become part of the monitoring dashboard in Response 3.
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

export default function ConservationPage() {
  return (
    <AuthGuard>
      <ConservationContent />
    </AuthGuard>
  );
}
