"use client";

import { useEffect, useState } from "react";
import { ArrowLeftRight, CalendarClock } from "lucide-react";
import { AuthGuard } from "@/components/auth-guard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { domainApi, Loan } from "@/lib/domain-api";
import { useCurrentUser } from "@/components/auth-guard";
import { can } from "@/lib/permissions";

function LoansContent() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const user = useCurrentUser();

  async function load() {
    setLoading(true);

    try {
      setLoans(await domainApi.loans.list());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function advance(loan: Loan) {
    const transitions: Record<string, string> = {
      REQUESTED: "UNDER_REVIEW",
      UNDER_REVIEW: "APPROVED",
      APPROVED: "ACTIVE",
      ACTIVE: "RETURN_DUE",
      RETURN_DUE: "RETURNED",
    };

    const next = transitions[loan.status];

    if (!next) return;

    await domainApi.loans.updateStatus(loan.id, next);
    await load();
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <div className="flex items-center gap-3">
              <ArrowLeftRight className="h-6 w-6" />
              <h1 className="text-3xl font-semibold">Loans</h1>
            </div>

            <p className="mt-2 text-sm text-slate-500">
              Incoming and outgoing loan workflows.
            </p>
          </div>
          {can(user, "loans:write") && <Button>New loan</Button>}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Active workflow records</CardTitle>
          </CardHeader>

          <CardContent>
            {loading ? (
              <p className="text-sm text-slate-500">Loading loans…</p>
            ) : loans.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center">
                <p className="font-medium">No loans recorded</p>
                <p className="mt-1 text-sm text-slate-500">
                  Create the first institutional loan workflow.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {loans.map((loan) => (
                  <div
                    key={loan.id}
                    className="flex items-center justify-between rounded-lg border border-slate-200 p-4"
                  >
                    <div>
                      <p className="font-medium">Loan #{loan.id}</p>

                      <p className="mt-1 flex items-center gap-2 text-sm text-slate-500">
                        <CalendarClock className="h-4 w-4" />
                        {loan.start_date} → {loan.due_date}
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium">
                        {loan.status}
                      </span>

                      {can(user, "loans:write") &&
                        loan.status !== "RETURNED" &&
                        loan.status !== "CANCELLED" && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => advance(loan)}
                          >
                            Advance
                          </Button>
                        )}
                    </div>
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

export default function LoansPage() {
  return (
    <AuthGuard>
      <LoansContent />
    </AuthGuard>
  );
}
