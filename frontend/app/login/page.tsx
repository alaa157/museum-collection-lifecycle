"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Archive, ArrowRight, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@gmail.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await api.login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12">
      <div className="mx-auto flex min-h-[80vh] max-w-6xl items-center justify-center">
        <div className="grid w-full overflow-hidden rounded-2xl border border-slate-800 bg-white shadow-2xl lg:grid-cols-[1.1fr_0.9fr]">
          <section className="hidden bg-slate-900 p-12 text-white lg:flex lg:flex-col lg:justify-between">
            <div>
              <div className="mb-8 flex items-center gap-3">
                <div className="rounded-xl bg-white/10 p-3">
                  <Archive className="h-6 w-6" />
                </div>
                <span className="font-semibold tracking-wide">
                  Museum Collection Lifecycle
                </span>
              </div>

              <h1 className="max-w-xl text-4xl font-semibold leading-tight">
                A professional workspace for the complete life of every object.
              </h1>

              <p className="mt-6 max-w-lg leading-7 text-slate-300">
                Manage collections, responsibility, location, condition,
                provenance and institutional workflows from one platform.
              </p>
            </div>

            <div className="flex items-center gap-3 text-sm text-slate-300">
              <ShieldCheck className="h-5 w-5" />
              Role-based access and audited institutional workflows.
            </div>
          </section>

          <section className="p-8 sm:p-12">
            <Card className="border-0 shadow-none">
              <CardHeader className="px-0">
                <p className="mb-2 text-sm font-medium text-slate-500">
                  Institutional access
                </p>
                <CardTitle className="text-3xl">
                  Sign in to your workspace
                </CardTitle>
              </CardHeader>

              <CardContent className="px-0">
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div>
                    <label
                      htmlFor="email"
                      className="mb-2 block text-sm font-medium text-slate-700"
                    >
                      Email
                    </label>
                    <Input
                      id="email"
                      type="email"
                      autoComplete="username"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      required
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="password"
                      className="mb-2 block text-sm font-medium text-slate-700"
                    >
                      Password
                    </label>
                    <Input
                      id="password"
                      type="password"
                      autoComplete="current-password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      required
                    />
                  </div>

                  {error && (
                    <div
                      role="alert"
                      className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                    >
                      {error}
                    </div>
                  )}

                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full"
                    size="lg"
                  >
                    {loading ? "Signing in…" : "Sign in"}
                    {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </section>
        </div>
      </div>
    </main>
  );
}
