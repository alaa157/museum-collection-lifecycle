"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Database,
  Gauge,
  Radio,
  Server
} from "lucide-react";

import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/app-shell";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card";

const services = [
  ["Gateway", "http://127.0.0.1:8000/health"],
  ["Auth", "http://127.0.0.1:8001/health"],
  ["Collection", "http://127.0.0.1:8002/health"],
  ["Conservation", "http://127.0.0.1:8003/health"],
  ["Loans", "http://127.0.0.1:8004/health"],
  ["Notifications", "http://127.0.0.1:8005/health"],
  ["Audit", "http://127.0.0.1:8006/health"]
];

function SettingsContent() {
  const [health, setHealth] = useState<
    Record<string, boolean>
  >({});

  useEffect(() => {
    Promise.all(
      services.map(async ([name, url]) => {
        try {
          const response = await fetch(url);
          return [name, response.ok] as const;
        } catch {
          return [name, false] as const;
        }
      })
    ).then((results) => {
      setHealth(Object.fromEntries(results));
    });
  }, []);

  return (
    <div className="p-5 lg:p-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold">
            System settings
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Application infrastructure and operational status.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                Application services
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-3">
              {services.map(([name]) => (
                <div
                  key={name}
                  className="flex items-center justify-between rounded-lg border border-slate-200 p-3"
                >
                  <span className="text-sm">
                    {name}
                  </span>

                  <span
                    className={`rounded-full px-3 py-1 text-xs ${
                      health[name]
                        ? "bg-slate-900 text-white"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {health[name]
                      ? "Healthy"
                      : "Unavailable"}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Infrastructure</CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
              <Status
                icon={Database}
                label="PostgreSQL"
                value="Host service"
              />

              <Status
                icon={Gauge}
                label="Redis"
                value="Host service"
              />

              <Status
                icon={Radio}
                label="RabbitMQ"
                value="Host service"
              />

              <Status
                icon={Activity}
                label="Prometheus"
                value="Host service"
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Status({
  icon: Icon,
  label,
  value
}: {
  icon: typeof Database;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-200 p-4">
      <div className="flex items-center gap-3">
        <Icon className="h-5 w-5 text-slate-500" />
        <span className="text-sm font-medium">
          {label}
        </span>
      </div>

      <span className="text-xs text-slate-500">
        {value}
      </span>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <AuthGuard>
      <AppShell>
        <SettingsContent />
      </AppShell>
    </AuthGuard>
  );
}
