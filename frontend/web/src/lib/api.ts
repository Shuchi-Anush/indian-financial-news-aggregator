import { Article, CursorPage, DashboardStats } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  async getArticles(params?: {
    cursor?: string;
    limit?: number;
    q?: string;
    source?: string[];
  }): Promise<CursorPage<Article>> {
    const url = new URL(`${API_BASE_URL}/articles`);
    if (params?.cursor) url.searchParams.append('cursor', params.cursor);
    if (params?.limit) url.searchParams.append('limit', params.limit.toString());
    if (params?.q) url.searchParams.append('q', params.q);
    if (params?.source) {
      params.source.forEach((src) => url.searchParams.append('source', src));
    }

    const res = await fetch(url.toString(), { next: { revalidate: 60 } });
    if (!res.ok) throw new Error('Failed to fetch articles');
    return res.json();
  }

  async getDashboardStats(): Promise<DashboardStats> {
    const res = await fetch('/api/stats', { next: { revalidate: 30 } });
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  }

  async triggerIngestion(): Promise<{ status: string; message: string }> {
    const response = await fetch('/api/trigger', { method: 'POST' });
    if (!response.ok) throw new Error('Failed to trigger ingestion');
    return response.json();
  }
}

export const api = new ApiClient();
