"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Archive,
  ArrowLeftRight,
  Beaker,
  CalendarDays,
  CircleAlert,
  Landmark,
  PackageSearch,
  Warehouse
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

async function dashboardRequest() {
  const token = localStorage.getItem("museum_access_token");

  const response = await fetch("/api/v1/dashboard/summary", {
    headers: token
      ? {
          Authorization: `Bearer ${token}`
        }
      : {}
  });

  if (!response.ok) {
    throw new Error("Unable to load dashboard.");
  }

  return response.json();
}

function DashboardContent() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: dashboardRequest,
    refetchInterval: 30_000
  });

  if (isLoading) {
    return (
      <div className="p-6 lg:p-10">
        Loading institutional dashboard…
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6 lg:p-10">
        <Card>
          <CardContent className="p-8 text-sm text-red-600">
            Dashboard data could not be loaded.
          </CardContent>
        </Card>
      </div>
    );
  }

  const summary = data?.summary ?? {};
  const collection = data?.collection ?? {};
  const conservation = data?.conservation ?? {};

  const statusData = collection.by_status ?? [];
  const typeData = collection.by_object_type ?? [];

  const metricCards = [
    {
      label: "Total collection",
      value: summary.total_items ?? 0,
      icon: Landmark
    },
    {
      label: "On display",
      value: summary.on_display ?? 0,
      icon: Archive
    },
    {
      label: "In storage",
      value: summary.in_storage ?? 0,
      icon: Warehouse
    },
    {
      label: "Under conservation",
      value: summary.under_conservation ?? 0,
      icon: Beaker
    },
    {
      label: "Active loans",
      value: summary.active_loans ?? 0,
      icon: ArrowLeftRight
    },
    {
      label: "Overdue loans",
      value: summary.overdue_loans ?? 0,
      icon: CircleAlert
    },
    {
      label: "Upcoming exhibitions",
      value: summary.upcoming_exhibitions ?? 0,
      icon: CalendarDays
    },
    {
      label: "Environment warnings",
      value: summary.environmental_warnings ?? 0,
      icon: CircleAlert
    }
  ];

  return (
    <div className="p-5 lg:p-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-slate-500">
            Institutional overview
          </p>

          <h1 className="mt-1 text-3xl font-semibold tracking-tight">
            Collection workspace
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Current collection, conservation, loan and environmental activity.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {metricCards.map((metric) => {
            const Icon = metric.icon;

            return (
              <Card key={metric.label}>
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-slate-500">
                        {metric.label}
                      </p>

                      <p className="mt-2 text-3xl font-semibold">
                        {metric.value}
                      </p>
                    </div>

                    <div className="rounded-lg bg-slate-100 p-3">
                      <Icon className="h-5 w-5 text-slate-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Collection by status</CardTitle>
            </CardHeader>

            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={statusData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Collection by object type</CardTitle>
            </CardHeader>

            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={typeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Conservation workload</CardTitle>
            </CardHeader>

            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">
                    Planned
                  </p>
                  <p className="mt-1 text-2xl font-semibold">
                    {conservation.planned_treatments ?? 0}
                  </p>
                </div>

                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">
                    In progress
                  </p>
                  <p className="mt-1 text-2xl font-semibold">
                    {conservation.treatments_in_progress ?? 0}
                  </p>
                </div>

                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">
                    Completed
                  </p>
                  <p className="mt-1 text-2xl font-semibold">
                    {conservation.completed_treatments ?? 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Operational health</CardTitle>
            </CardHeader>

            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">
                    Collection indexing
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs">
                    Operational
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">
                    Event processing
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs">
                    RabbitMQ
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">
                    Cache
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs">
                    Redis
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <AppShell>
        <DashboardContent />
      </AppShell>
    </AuthGuard>
  );
}
