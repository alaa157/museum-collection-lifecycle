"use client";

import { FormEvent, useEffect, useState } from "react";
import { CalendarRange, Plus } from "lucide-react";

import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { domainApi } from "@/lib/domain-api";
import { useCurrentUser } from "@/components/auth-guard";
import { can } from "@/lib/permissions";

function ExhibitionsContent() {
  const [exhibitions, setExhibitions] = useState<any[]>([]);
  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const user = useCurrentUser();

  async function load() {
    setExhibitions(await domainApi.loans.exhibitions());
  }

  useEffect(() => {
    load();
  }, []);

  async function create(event: FormEvent) {
    event.preventDefault();

    await domainApi.loans.createExhibition({
      title,
      curator_id: 1,
      start_date: startDate,
      end_date: endDate,
      location,
      description: null,
    });

    setTitle("");
    setLocation("");
    setStartDate("");
    setEndDate("");

    await load();
  }

  async function activate(id: number) {
    await domainApi.loans.updateExhibitionStatus(id, "ACTIVE");

    await load();
  }

  async function complete(id: number) {
    await domainApi.loans.updateExhibitionStatus(id, "COMPLETED");

    await load();
  }

  return (
    <div className="p-5 lg:p-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <CalendarRange className="h-6 w-6" />
            <h1 className="text-3xl font-semibold">Exhibitions</h1>
          </div>

          <p className="mt-2 text-sm text-slate-500">
            Plan, activate and complete exhibition records.
          </p>
        </div>

        <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                New exhibition
              </CardTitle>
            </CardHeader>

            <CardContent>
              <form onSubmit={create} className="space-y-4">
                <Input
                  placeholder="Exhibition title"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  required
                />

                <Input
                  placeholder="Location"
                  value={location}
                  onChange={(event) => setLocation(event.target.value)}
                  required
                />

                <Input
                  type="date"
                  value={startDate}
                  onChange={(event) => setStartDate(event.target.value)}
                  required
                />

                <Input
                  type="date"
                  value={endDate}
                  onChange={(event) => setEndDate(event.target.value)}
                  required
                />

                {can(user, "exhibitions:write") && <Button>New loan</Button>}
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Exhibition programme</CardTitle>
            </CardHeader>

            <CardContent className="p-0">
              {exhibitions.length === 0 ? (
                <div className="p-8 text-center text-sm text-slate-500">
                  No exhibitions have been created.
                </div>
              ) : (
                <div className="divide-y divide-slate-200">
                  {exhibitions.map((item) => (
                    <div
                      key={item.id}
                      className="space-y-4 p-5 sm:flex sm:items-center sm:justify-between sm:space-y-0"
                    >
                      <div>
                        <p className="font-semibold">{item.title}</p>

                        <p className="mt-1 text-sm text-slate-500">
                          {item.start_date} → {item.end_date}
                        </p>

                        <p className="mt-1 text-sm text-slate-500">
                          {item.location}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs">
                          {item.status}
                        </span>

                        {item.status === "PLANNED" &&
                          can(user, "exhibitions:write") && (
                            <Button size="sm" onClick={() => activate(item.id)}>
                              Activate
                            </Button>
                          )}

                        {item.status === "ACTIVE" &&
                          can(user, "exhibitions:write") && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => complete(item.id)}
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
    </div>
  );
}

export default function ExhibitionsPage() {
  return (
    <AuthGuard>
      <AppShell>
        <ExhibitionsContent />
      </AppShell>
    </AuthGuard>
  );
}
