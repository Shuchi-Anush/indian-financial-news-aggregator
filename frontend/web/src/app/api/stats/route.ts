import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ADMIN_API_KEY = process.env.ADMIN_API_KEY || '';

export const revalidate = 30; // 30 seconds caching

export async function GET() {
  if (!ADMIN_API_KEY) {
    return NextResponse.json({ error: 'ADMIN_API_KEY is not configured on the server.' }, { status: 500 });
  }

  try {
    const res = await fetch(`${API_BASE_URL}/admin/dashboard/stats`, {
      headers: {
        'X-API-Key': ADMIN_API_KEY,
      },
      next: { revalidate: 30 }
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Backend responded with ${res.status}: ${text}`);
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Stats proxy error:', error);
    return NextResponse.json({ error: 'Failed to fetch dashboard stats' }, { status: 500 });
  }
}
