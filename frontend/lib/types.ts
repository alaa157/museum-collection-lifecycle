export type Permission = {
  code: string;
  description: string | null;
};

export type Role = {
  name: string;
  description: string | null;
  permissions: Permission[];
};

export type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_verified: boolean;
  roles: Role[];
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};
