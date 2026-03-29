/** ユーザー */
export interface User {
  id: number;
  name: string;
  email: string;
  role: "admin" | "viewer";
  notification_settings_json: Record<string, unknown> | null;
  created_at: string;
}

/** 認証レスポンス */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/** 企業 */
export interface Company {
  id: number;
  name: string;
  category: string;
  website_url: string | null;
  logo_url: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** クロールソース */
export interface CrawlSource {
  id: number;
  company_id: number;
  source_type: string;
  url: string;
  crawl_frequency: string;
  last_crawled_at: string | null;
  is_active: boolean;
}
