"use client";

import { FormEvent, useState } from "react";
import { ArrowLeft, FilePlus2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { domainApi } from "@/lib/domain-api";
import { useCurrentUser } from "@/components/auth-guard";
import { can } from "@/lib/permissions";

function AcquisitionsContent() {
  const router = useRouter();

  const [itemId, setItemId] = useState("");
  const [source, setSource] = useState("");
  const [date, setDate] = useState("");
  const [type, setType] = useState("DONATION");
  const [price, setPrice] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [message, setMessage] = useState("");

  const user = useCurrentUser();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");

    try {
      const token = localStorage.getItem("museum_access_token");

      const response = await fetch(
        `/api/v1/collection/items/${itemId}/acquisitions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token
              ? {
                  Authorization: `Bearer ${token}`,
                }
              : {}),
          },
          body: JSON.stringify({
            acquisition_type: type,
            acquisition_date: date,
            source,
            price: price ? Number(price) : null,
            currency: currency || null,
          }),
        },
      );

      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.detail || "Unable to save acquisition.");
      }

      setMessage("Acquisition record created.");
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Unable to create acquisition.",
      );
    }
  }

  return (
    <div className="p-5 lg:p-10">
      <div className="mx-auto max-w-3xl">
        <Button variant="ghost" onClick={() => router.push("/dashboard")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <div className="mb-6 mt-5">
          <div className="flex items-center gap-3">
            <FilePlus2 className="h-6 w-6" />
            <h1 className="text-3xl font-semibold">Acquisition record</h1>
          </div>

          <p className="mt-2 text-sm text-slate-500">
            Record the institutional acquisition history of an object.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Acquisition details</CardTitle>
          </CardHeader>

          <CardContent>
            <form onSubmit={submit} className="space-y-5">
              <Input
                placeholder="Collection item UUID"
                value={itemId}
                onChange={(event) => setItemId(event.target.value)}
                required
              />

              <select
                className="h-10 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm"
                value={type}
                onChange={(event) => setType(event.target.value)}
              >
                <option value="PURCHASE">Purchase</option>
                <option value="DONATION">Donation</option>
                <option value="BEQUEST">Bequest</option>
                <option value="TRANSFER">Transfer</option>
                <option value="EXCAVATION">Excavation</option>
                <option value="FOUND_IN_COLLECTION">Found in collection</option>
                <option value="OTHER">Other</option>
              </select>

              <Input
                type="date"
                value={date}
                onChange={(event) => setDate(event.target.value)}
                required
              />

              <Input
                placeholder="Source"
                value={source}
                onChange={(event) => setSource(event.target.value)}
                required
              />

              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  type="number"
                  min="0"
                  placeholder="Price"
                  value={price}
                  onChange={(event) => setPrice(event.target.value)}
                />

                <Input
                  maxLength={3}
                  placeholder="Currency"
                  value={currency}
                  onChange={(event) =>
                    setCurrency(event.target.value.toUpperCase())
                  }
                />
              </div>
              {can(user, "acquisitions.create") && (
                <Button type="submit">Create acquisition</Button>
              )}

              {message && <p className="text-sm text-slate-600">{message}</p>}
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function AcquisitionsPage() {
  return (
    <AuthGuard>
      <AppShell>
        <AcquisitionsContent />
      </AppShell>
    </AuthGuard>
  );
}
