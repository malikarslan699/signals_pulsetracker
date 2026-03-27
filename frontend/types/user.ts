export interface User {
  id: string;
  email: string;
  username: string;
  role: "user" | "premium" | "admin" | "owner" | "superadmin" | "reseller";
  plan: "trial" | "monthly" | "yearly" | "lifetime";
  plan_expires_at?: string;
  market_access?: "crypto" | "forex" | "both";
  telegram_chat_id?: number;
  is_verified?: boolean;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token?: string | null;
  refresh_token?: string | null;
  token_type: string;
  expires_in: number;
  user?: User;
  requires_email_verification?: boolean;
  verification_email_sent?: boolean;
  message?: string | null;
}
