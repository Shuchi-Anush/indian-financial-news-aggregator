# Frontend Architecture Roadmap

This document outlines the operational status and strategic roadmap for the presentation layer of the Indian Financial News Aggregator.

## Current Validation Dashboard

The frontend is currently implemented as a **Streamlit** dashboard. 

Streamlit is utilized strictly as an **Operational Validation Layer**. It exists solely to allow backend engineers to visually verify that the ingestion orchestration, deduplication hashing, database constraints, and API pagination are behaving correctly in deployment. 

## Current Data Flow

The Streamlit dashboard operates as a stateless HTTP client. It executes linearly on every interaction, issuing asynchronous `GET` requests to the FastAPI backend (`http://backend:8000`). It holds no domain logic and relies entirely on the API for pagination, sorting, search execution, and materialized view querying.

## Limitations

Streamlit is not a production-grade consumer framework. It exhibits intentional engineering limitations:
- **Re-execution Model**: The entire application script evaluates top-to-bottom on every user interaction, generating unacceptable UI latency.
- **Lack of SSR**: Server-Side Rendering is impossible, preventing SEO indexing.
- **State Ephemerality**: Client state cannot be durably managed without complex session hacking.

## Next.js Architecture Vision

The future presentation layer will be implemented in **Next.js** (App Router). This migration will establish a decoupled, highly performant frontend capable of handling consumer traffic safely.

## API Consumption Strategy

The Next.js application will utilize React Server Components (RSC) to execute data fetching securely on the server. This prevents exposing the underlying FastAPI endpoints directly to the browser and drastically reduces the JavaScript bundle size shipped to the client edge.

## Caching Strategy

The Next.js fetch layer will cache static endpoints heavily:
- Analytical routes (e.g., `GET /api/analytics/trending`) will utilize Time-Based Revalidation (`revalidate: 3600`) to cache aggregates.
- Dynamic routes (e.g., search queries) will utilize `cache: 'no-store'` to fetch fresh data via keyset pagination.

## Authentication Strategy

**NextAuth.js** will be integrated to handle session negotiation. The Next.js server will act as the authentication boundary, generating session tokens that are forwarded to the FastAPI backend to enforce Role-Based Access Control (RBAC) on premium features like bulk CSV exports.

## State Management

1. **Server State**: Managed natively via RSC fetch caching.
2. **URL State**: Query parameters (search arguments, pagination cursors) will be pushed to the URL for deep-linking and browser history support.
3. **Client State**: Minimal. Local UI toggles (dark mode, menus) will be handled via standard React Context or Zustand.

## Future UI Roadmap

1. **Bootstrap Next.js Workspace**: Initialize the App Router alongside the Streamlit directory.
2. **Component Implementation**: Construct accessible data tables utilizing TanStack Table and Tailwind CSS.
3. **Data Fetching Migration**: Port the Streamlit `httpx` logic to RSC native `fetch` requests.
4. **Proxy Re-routing**: Update Nginx to route `/` traffic to the Next.js container, bypassing Streamlit.
5. **Streamlit Deprecation**: Fully remove the Streamlit container from the orchestration manifest.
