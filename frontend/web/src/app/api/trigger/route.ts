import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ADMIN_API_KEY = process.env.ADMIN_API_KEY || '';

export async function POST() {
  if (!ADMIN_API_KEY) {
    return NextResponse.json({ error: 'ADMIN_API_KEY is not configured on the server.' }, { status: 500 });
  }

  try {
    const res = await fetch(`${API_BASE_URL}/admin/pipeline/trigger`, {
      method: 'POST',
      headers: {
        'X-API-Key': ADMIN_API_KEY,
        'Content-Type': 'application/json',
      },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Backend responded with ${res.status}: ${text}`);
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Trigger proxy error:', error);
    return NextResponse.json({ error: 'Failed to trigger ingestion' }, { status: 500 });
  }
}
