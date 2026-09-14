export type User = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
};


export type Session = {
  accessToken: string;
  refreshToken?: string;
  user: User;
};