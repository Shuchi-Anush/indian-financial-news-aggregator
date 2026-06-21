'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Article, DashboardStats } from '@/types';
import { ArticleCard } from '@/components/features/ArticleCard';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Search, Download, BarChart2 } from 'lucide-react';

export default function Home() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [query, setQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardStats().then(setStats).catch(console.error);
  }, []);

  useEffect(() => {
    let active = true;
    api.getArticles({ q: query, limit: 12 })
      .then((res) => {
        if (active) setArticles(res.items);
      })
      .catch(console.error)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [query]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setQuery(searchInput);
  };

  const handleExportCSV = () => {
    const url = new URL(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/articles/export/csv`);
    if (query) url.searchParams.append('q', query);
    window.open(url.toString(), '_blank');
  };

  const handleExportExcel = () => {
    const url = new URL(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/articles/export/xlsx`);
    if (query) url.searchParams.append('q', query);
    window.open(url.toString(), '_blank');
  };

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Dashboard Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
            <BarChart2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_articles ?? '-'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_sources ?? '-'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Articles Today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.articles_today ?? '-'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Ingestion</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-bold truncate">
              {stats?.last_ingestion ? new Date(stats.last_ingestion).toLocaleString() : '-'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter & Export Bar */}
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <form onSubmit={handleSearch} className="flex w-full md:w-1/2 space-x-2">
          <Input 
            placeholder="Search financial news..." 
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <Button type="submit">
            <Search className="mr-2 h-4 w-4" />
            Search
          </Button>
        </form>
        <div className="flex space-x-2 w-full md:w-auto justify-end">
          <Button variant="outline" onClick={handleExportCSV}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
          <Button variant="outline" onClick={handleExportExcel}>
            <Download className="mr-2 h-4 w-4" />
            Export Excel
          </Button>
        </div>
      </div>

      {/* Articles Grid */}
      {loading ? (
        <div className="text-center py-12 text-muted-foreground">Loading articles...</div>
      ) : articles.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">No articles found. Try adjusting your search.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
