"use client";

import { useEffect, useState } from "react";
import { Shield, UserPlus, Users as UsersIcon } from "lucide-react";

import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getAccessToken } from "@/lib/auth";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();

  const response = await fetch(
    `/api/v1${path}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token
          ? {
              Authorization: `Bearer ${token}`
            }
          : {}),
        ...options.headers
      }
    }
  );

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      body.detail ||
        body.error?.message ||
        "Request failed."
    );
  }

  return response.json();
}

function UsersContent() {
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("VIEWER");
  const [message, setMessage] = useState("");

  async function load() {
    const [loadedUsers, loadedRoles] = await Promise.all([
      request<any[]>("/auth/users"),
      request<any[]>("/auth/roles")
    ]);

    setUsers(loadedUsers);
    setRoles(loadedRoles);
  }

  useEffect(() => {
    load().catch((err) => setMessage(err.message));
  }, []);

  async function createUser() {
    setMessage("");

    try {
      await request("/auth/users", {
        method: "POST",
        body: JSON.stringify({
          email,
          first_name: firstName,
          last_name: lastName,
          password,
          role_names: [role]
        })
      });

      setEmail("");
      setFirstName("");
      setLastName("");
      setPassword("");

      await load();

      setMessage("User created.");
    } catch (err) {
      setMessage(
        err instanceof Error
          ? err.message
          : "Unable to create user."
      );
    }
  }

  return (
    <div className="p-5 lg:p-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <UsersIcon className="h-6 w-6" />
            <h1 className="text-3xl font-semibold">
              Users & roles
            </h1>
          </div>

          <p className="mt-2 text-sm text-slate-500">
            Manage institutional identities and access roles.
          </p>
        </div>

        <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserPlus className="h-5 w-5" />
                Create user
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
              <Input
                placeholder="First name"
                value={firstName}
                onChange={(event) =>
                  setFirstName(event.target.value)
                }
              />

              <Input
                placeholder="Last name"
                value={lastName}
                onChange={(event) =>
                  setLastName(event.target.value)
                }
              />

              <Input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
              />

              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
              />

              <select
                className="h-10 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm"
                value={role}
                onChange={(event) =>
                  setRole(event.target.value)
                }
              >
                {roles.map((item) => (
                  <option
                    key={item.name}
                    value={item.name}
                  >
                    {item.name}
                  </option>
                ))}
              </select>

              <Button
                className="w-full"
                onClick={createUser}
                disabled={
                  !email ||
                  !firstName ||
                  !lastName ||
                  !password
                }
              >
                Create user
              </Button>

              {message && (
                <p className="text-sm text-slate-600">
                  {message}
                </p>
              )}
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Users</CardTitle>
              </CardHeader>

              <CardContent className="p-0">
                <div className="divide-y divide-slate-200">
                  {users.map((user) => (
                    <div
                      key={user.id}
                      className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <p className="font-medium">
                          {user.first_name} {user.last_name}
                        </p>

                        <p className="text-sm text-slate-500">
                          {user.email}
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center gap-2">
                        {user.roles.map(
                          (item: any) => (
                            <span
                              key={item.name}
                              className="rounded-full bg-slate-100 px-3 py-1 text-xs"
                            >
                              {item.name}
                            </span>
                          )
                        )}

                        <span
                          className={`rounded-full px-3 py-1 text-xs ${
                            user.is_active
                              ? "bg-slate-900 text-white"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          {user.is_active
                            ? "Active"
                            : "Inactive"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Roles
                </CardTitle>
              </CardHeader>

              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  {roles.map((item) => (
                    <div
                      key={item.name}
                      className="rounded-lg border border-slate-200 p-4"
                    >
                      <p className="font-medium">
                        {item.name}
                      </p>

                      <p className="mt-1 text-sm text-slate-500">
                        {item.description}
                      </p>

                      <p className="mt-3 text-xs text-slate-400">
                        {item.permissions?.length ?? 0} permissions
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function UsersPage() {
  return (
    <AuthGuard>
      <AppShell>
        <UsersContent />
      </AppShell>
    </AuthGuard>
  );
}
