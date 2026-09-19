"use client";

import { use, useEffect, useState, useRef } from "react";
import Link from "next/link";
import { ArrowLeft, MapPin } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AuthGuard } from "@/components/auth-guard";
import {
  domainApi,
  CollectionItem,
  ConditionReport,
  Treatment,
} from "@/lib/domain-api";
import { useCurrentUser } from "@/components/auth-guard";
import { can } from "@/lib/permissions";

type AttachmentItem = {
  id: number;
  original_filename: string;
  mime_type: string;
  uploaded_at: string;
};

function DigitalAssets({ itemId }: { itemId: string }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const user = useCurrentUser();

  async function loadAttachments() {
    const token = localStorage.getItem("museum_access_token");
    const response = await fetch(
      `/api/v1/collection/items/${itemId}/attachments`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} },
    );
    if (response.ok) setAttachments(await response.json());
  }

  useEffect(() => {
    loadAttachments();
  }, [itemId]);

  useEffect(() => {
    let objectUrl: string | null = null;

    async function loadQr() {
      const token = localStorage.getItem("museum_access_token");

      const response = await fetch(`/api/v1/collection/items/${itemId}/qr`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) return;

      const blob = await response.blob();
      objectUrl = URL.createObjectURL(blob);
      setQrUrl(objectUrl);
    }

    loadQr();

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [itemId]);

  async function upload() {
    const file = fileInput.current?.files?.[0];

    if (!file) {
      setError("Select a file first.");
      return;
    }

    const token = localStorage.getItem("museum_access_token");

    const form = new FormData();
    form.append("file", file);

    setUploading(true);
    setError("");

    try {
      const response = await fetch(
        `/api/v1/collection/items/${itemId}/attachments`,
        {
          method: "POST",
          headers: token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : {},
          body: form,
        },
      );

      if (!response.ok) {
        const body = await response.json();

        throw new Error(body.detail || "Unable to upload file.");
      }

      if (fileInput.current) {
        fileInput.current.value = "";
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to upload file.");
    } finally {
      setUploading(false);
    }
  }
  async function downloadAttachment(id: number, filename: string) {
    const token = localStorage.getItem("museum_access_token");
    const response = await fetch(
      `/api/v1/collection/attachments/${id}/download`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} },
    );
    if (!response.ok) return;
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function printQr() {
    const image = document.getElementById("collection-qr");

    if (!image) return;

    const popup = window.open("", "qr-print", "width=600,height=700");

    if (!popup) return;

    popup.document.write(`
      <html>
        <body style="display:flex;justify-content:center;align-items:center;height:100vh">
          <img src="${image.getAttribute("src")}" style="max-width:500px" />
        </body>
      </html>
    `);

    popup.document.close();
    popup.focus();
    popup.print();
  }

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Object QR code</CardTitle>
        </CardHeader>

        <CardContent>
          <img
            id="collection-qr"
            src={qrUrl ?? ""}
            alt="Collection item QR code"
            className="mx-auto h-48 w-48"
          />

          <div className="mt-4 flex gap-2">
            <a
              href={qrUrl ?? ""}
              download={`collection-${itemId}.png`}
              className="flex-1"
            >
              <Button variant="outline" className="w-full">
                Download
              </Button>
            </a>

            <Button className="flex-1" onClick={printQr}>
              Print
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Digital assets</CardTitle>
        </CardHeader>

        <CardContent>
          <input
            ref={fileInput}
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            className="w-full rounded-lg border border-slate-300 p-2 text-sm"
          />

          <Button className="mt-3 w-full" onClick={upload} disabled={uploading}>
            {uploading ? "Uploading…" : "Upload asset"}
          </Button>

          <ul className="mt-4 space-y-2 text-sm">
            {attachments.map((a) => (
              <li key={a.id} className="flex items-center justify-between">
                <span className="truncate">{a.original_filename}</span>
                <button
                  onClick={() => downloadAttachment(a.id, a.original_filename)}
                  className="text-blue-600 underline"
                >
                  Download
                </button>
              </li>
            ))}
          </ul>

          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}

function ItemContent({ id }: { id: string }) {
  const [item, setItem] = useState<CollectionItem | null>(null);
  const [provenance, setProvenance] = useState<any[]>([]);
  const [reports, setReports] = useState<ConditionReport[]>([]);
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [loading, setLoading] = useState(true);
  const user = useCurrentUser();
  useEffect(() => {
    async function load() {
      try {
        const [loadedItem, loadedProvenance, loadedReports, loadedTreatments] =
          await Promise.all([
            domainApi.collection.get(id),
            domainApi.collection.provenance(id),
            domainApi.conservation.conditionReports(id),
            domainApi.conservation.treatments(id),
          ]);

        setItem(loadedItem);
        setProvenance(loadedProvenance);
        setReports(loadedReports);
        setTreatments(loadedTreatments);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id]);

  if (loading) {
    return (
      <div className="p-10 text-sm text-slate-500">Loading object record…</div>
    );
  }

  if (!item) {
    return (
      <div className="p-10 text-center">
        <p className="font-semibold">Object not found</p>
        <Link
          href="/collection"
          className="mt-2 inline-block text-sm underline"
        >
          Return to collection
        </Link>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center px-6 py-4">
          <Link href="/collection">
            {can(user, "collection:read") && (
            <Button variant="ghost">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Collection
            </Button>
            )}
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <div>
            <div className="mb-6">
              <p className="text-sm text-slate-500">{item.accession_number}</p>

              <h1 className="mt-1 text-4xl font-semibold tracking-tight">
                {item.title}
              </h1>

              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-medium text-white">
                  {item.status.replaceAll("_", " ")}
                </span>

                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  Object {item.object_number}
                </span>
              </div>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Record overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-6 sm:grid-cols-2">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      Accession number
                    </p>
                    <p className="mt-1 font-medium">{item.accession_number}</p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      Object number
                    </p>
                    <p className="mt-1 font-medium">{item.object_number}</p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      Current location
                    </p>
                    <p className="mt-1 flex items-center gap-2 font-medium">
                      <MapPin className="h-4 w-4 text-slate-400" />
                      {item.current_location_id ?? "Unassigned"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      Value
                    </p>
                    <p className="mt-1 font-medium">
                      {item.value == null
                        ? "Not recorded"
                        : item.value.toLocaleString()}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Provenance timeline</CardTitle>
              </CardHeader>

              <CardContent>
                {provenance.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No provenance records have been recorded.
                  </p>
                ) : (
                  <div className="space-y-6">
                    {provenance.map((record) => (
                      <div
                        key={record.id}
                        className="relative border-l-2 border-slate-200 pl-5"
                      >
                        <p className="font-medium">{record.previous_owner}</p>
                        <p className="mt-1 text-sm text-slate-500">
                          {record.ownership_period ||
                            record.record_date ||
                            "Period not specified"}
                        </p>
                        {record.geographic_location && (
                          <p className="mt-2 text-sm text-slate-700">
                            {record.geographic_location}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Condition history</CardTitle>
              </CardHeader>

              <CardContent>
                {reports.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No condition reports have been recorded.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {reports.map((report) => (
                      <div
                        key={report.id}
                        className="rounded-lg border border-slate-200 p-4"
                      >
                        <div className="flex items-center justify-between">
                          <p className="font-medium">
                            Score {report.condition_score}
                          </p>
                          <span className="text-xs text-slate-500">
                            {report.report_date}
                          </span>
                        </div>

                        {report.observed_damage && (
                          <p className="mt-3 text-sm text-slate-600">
                            {report.observed_damage}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Conservation treatments</CardTitle>
              </CardHeader>

              <CardContent>
                {treatments.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No conservation treatments have been recorded.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {treatments.map((treatment) => (
                      <div
                        key={treatment.id}
                        className="flex items-center justify-between rounded-lg border border-slate-200 p-4"
                      >
                        <div>
                          <p className="font-medium">
                            {treatment.treatment_type}
                          </p>
                          <p className="mt-1 text-sm text-slate-500">
                            {treatment.start_date || "Start date pending"}
                          </p>
                        </div>

                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs">
                          {treatment.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <aside className="space-y-5">
            <DigitalAssets itemId={id} />

            <Card>
              <CardContent className="p-5">
                <Link
                  href={`/audit?entity_id=${encodeURIComponent(id)}`}
                  className="block"
                >
                  {can(user, "audit:read") && (
                  <Button variant="outline" className="w-full">
                    Audit history
                  </Button>
                  )}
                </Link>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </main>
  );
}

export default function CollectionItemPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return (
    <AuthGuard>
      <ItemContent id={id} />
    </AuthGuard>
  );
}
