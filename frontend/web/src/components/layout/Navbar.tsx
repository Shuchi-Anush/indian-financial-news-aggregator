'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';

import Link from 'next/link';

export function Navbar() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleTrigger = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await api.triggerIngestion();
      setMessage(res.message || 'Started collection cycle.');
    } catch {
      setMessage('Failed to trigger ingestion.');
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center px-4 mx-auto justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/" className="font-bold tracking-tight">Financial News Aggregator</Link>
        </div>
        <div className="flex items-center space-x-4">
          {message && <span className="text-sm text-muted-foreground mr-4">{message}</span>}
          <Button onClick={handleTrigger} disabled={loading} variant="outline" size="sm">
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Fetch Latest News
          </Button>
        </div>
      </div>
    </nav>
  );
}
