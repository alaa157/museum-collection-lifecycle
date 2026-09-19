"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save } from "lucide-react";

import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { domainApi } from "@/lib/domain-api";

function NewCollectionItemContent() {
  const router = useRouter();

  const [form, setForm] = useState({
    accession_number: "",
    object_number: "",
    title: "",
    description: "",
    classification: "",
    place_of_origin: "",
    period_date: "",
    legal_status: "",
    current_condition: "",
    value: "",
    insurance_value: ""
  });

  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function update(
    field: keyof typeof form,
    value: string
  ) {
    setForm((current) => ({
      ...current,
      [field]: value
    }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();

    setSaving(true);
    setError("");

    try {
      const item = await domainApi.collection.create({
        accession_number: form.accession_number,
        object_number: form.object_number,
        title: form.title,
        description: form.description || null,
        classification: form.classification || null,
        place_of_origin: form.place_of_origin || null,
        period_date: form.period_date || null,
        legal_status: form.legal_status || null,
        current_condition: form.current_condition || null,
        value: form.value
          ? Number(form.value)
          : null,
        insurance_value: form.insurance_value
          ? Number(form.insurance_value)
          : null
      });

      router.push(`/collection/${item.id}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create collection item."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-5 lg:p-10">
      <div className="mx-auto max-w-4xl">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => router.push("/collection")}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Collection
          </Button>

          <h1 className="mt-4 text-3xl font-semibold">
            Register collection item
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Create an institutional object record.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Catalog record</CardTitle>
          </CardHeader>

          <CardContent>
            <form onSubmit={submit} className="space-y-6">
              <div className="grid gap-5 md:grid-cols-2">
                <Field
                  label="Accession number"
                  value={form.accession_number}
                  onChange={(value) =>
                    update("accession_number", value)
                  }
                  required
                />

                <Field
                  label="Object number"
                  value={form.object_number}
                  onChange={(value) =>
                    update("object_number", value)
                  }
                  required
                />

                <div className="md:col-span-2">
                  <Field
                    label="Title"
                    value={form.title}
                    onChange={(value) =>
                      update("title", value)
                    }
                    required
                  />
                </div>

                <Field
                  label="Classification"
                  value={form.classification}
                  onChange={(value) =>
                    update("classification", value)
                  }
                />

                <Field
                  label="Period / date"
                  value={form.period_date}
                  onChange={(value) =>
                    update("period_date", value)
                  }
                />

                <Field
                  label="Place of origin"
                  value={form.place_of_origin}
                  onChange={(value) =>
                    update("place_of_origin", value)
                  }
                />

                <Field
                  label="Current condition"
                  value={form.current_condition}
                  onChange={(value) =>
                    update("current_condition", value)
                  }
                />

                <Field
                  label="Value"
                  type="number"
                  value={form.value}
                  onChange={(value) =>
                    update("value", value)
                  }
                />

                <Field
                  label="Insurance value"
                  type="number"
                  value={form.insurance_value}
                  onChange={(value) =>
                    update("insurance_value", value)
                  }
                />

                <Field
                  label="Legal status"
                  value={form.legal_status}
                  onChange={(value) =>
                    update("legal_status", value)
                  }
                />
              </div>

              <div>
                <label
                  htmlFor="description"
                  className="mb-2 block text-sm font-medium"
                >
                  Description
                </label>

                <textarea
                  id="description"
                  className="min-h-32 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-slate-500"
                  value={form.description}
                  onChange={(event) =>
                    update(
                      "description",
                      event.target.value
                    )
                  }
                />
              </div>

              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={saving}
                >
                  <Save className="mr-2 h-4 w-4" />
                  {saving
                    ? "Creating…"
                    : "Create object"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  required,
  type = "text"
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: string;
}) {
  const id = label
    .toLowerCase()
    .replaceAll(" ", "-")
    .replaceAll("/", "-");

  return (
    <div>
      <label
        htmlFor={id}
        className="mb-2 block text-sm font-medium"
      >
        {label}
      </label>

      <Input
        id={id}
        type={type}
        value={value}
        required={required}
        onChange={(event) =>
          onChange(event.target.value)
        }
      />
    </div>
  );
}

export default function NewCollectionItemPage() {
  return (
    <AuthGuard>
      <AppShell>
        <NewCollectionItemContent />
      </AppShell>
    </AuthGuard>
  );
}
