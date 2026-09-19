import type { User } from "@/lib/types";

export function userPermissions(user: User | null | undefined): Set<string> {
  const codes = new Set<string>();
  if (!user) return codes;
  for (const role of user.roles ?? []) {
    for (const p of role.permissions ?? []) {
      if (p.code) codes.add(p.code);
    }
  }
  return codes;
}

export function can(user: User | null | undefined, permission: string): boolean {
  return userPermissions(user).has(permission);
}