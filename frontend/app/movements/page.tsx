"use client";

import { useEffect, useState } from "react";
import { Check, CircleX, MapPin } from "lucide-react";

import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { domainApi, MovementRequest } from "@/lib/domain-api";
import { ca } from "zod/v4/locales";
import { useCurrentUser } from "@/components/auth-guard";
import { can } from "@/lib/permissions";

function MovementsContent() {
  const [movements, setMovements] = useState<MovementRequest[]>([]);
  const [error, setError] = useState("");
  const user = useCurrentUser();

  async function load() {
    try {
      setMovements(await domainApi.collection.movements());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load movements.",
      );
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function update(id: number, status: string) {
    await domainApi.collection.movementStatus(id, status);

    await load();
  }

  return (
    <div className="p-5 lg:p-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <MapPin className="h-6 w-6" />
            <h1 className="text-3xl font-semibold">Movement requests</h1>
          </div>

          <p className="mt-2 text-sm text-slate-500">
            Review and progress collection movement workflows.
          </p>
        </div>

        {error && (
          <Card className="mb-5">
            <CardContent className="p-5 text-sm text-red-600">
              {error}
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Requests</CardTitle>
          </CardHeader>

          <CardContent className="p-0">
            {movements.length === 0 ? (
              <div className="p-8 text-center text-sm text-slate-500">
                No movement requests.
              </div>
            ) : (
              <div className="divide-y divide-slate-200">
                {movements.map((movement) => (
                  <div
                    key={movement.id}
                    className="space-y-4 p-5 lg:flex lg:items-center lg:justify-between lg:space-y-0"
                  >
                    <div>
                      <p className="font-medium">Movement #{movement.id}</p>

                      <p className="mt-1 text-sm text-slate-500">
                        Item {movement.collection_item_id}
                      </p>

                      <p className="mt-2 text-sm text-slate-600">
                        {movement.reason}
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium">
                        {movement.status}
                      </span>

                      {movement.status === "REQUESTED" && ( can(user, "movements:write") && (
                        <>
                          <Button
                            size="sm"
                            onClick={() => update(movement.id, "APPROVED")}
                          >
                            <Check className="mr-2 h-4 w-4" />
                            Approve
                          </Button>
                          {can(user, "movements:write") && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => update(movement.id, "REJECTED")}
                            >
                              <CircleX className="mr-2 h-4 w-4" />
                              Reject
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => update(movement.id, "REJECTED")}
                          >
                            <CircleX className="mr-2 h-4 w-4" />
                            Reject
                          </Button>
                        </>
                      ))}

                      {movement.status === "APPROVED" &&
                        can(user, "movements:write") && (
                          <Button
                            size="sm"
                            onClick={() => update(movement.id, "IN_TRANSIT")}
                          >
                            Start movement
                          </Button>
                        )}

                      {movement.status === "IN_TRANSIT" &&
                        can(user, "movements:write") && (
                          <Button
                            size="sm"
                            onClick={() => update(movement.id, "COMPLETED")}
                          >
                            Complete
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
    </div>
  );
}

export default function MovementsPage() {
  return (
    <AuthGuard>
      <AppShell>
        <MovementsContent />
      </AppShell>
    </AuthGuard>
  );
}
