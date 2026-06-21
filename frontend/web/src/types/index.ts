export interface Article {
  id: string;
  source_id: string;
  source_name: string;
  url: string;
  title: string;
  summary: string | null;
  author: string | null;
  published_at: string;
  category: string;
  sentiment_score: number | null;
  sentiment_label: string | null;
  created_at: string;
}

export interface CursorPage<T> {
  items: T[];
  meta: {
    next_cursor: string | null;
    has_more: boolean;
  };
}

export interface DashboardStats {
  total_articles: number;
  active_sources: number;
  articles_today: number;
  last_ingestion: string | null;
}
