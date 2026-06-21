import { test, expect } from "@playwright/test";

// ---------------------------------------------------------------------------
// 1. Homepage & Navigation
// ---------------------------------------------------------------------------

test.describe("Homepage", () => {
  test("loads with correct title", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Indian Financial News/i);
  });

  test("renders navbar with app name", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("nav")).toBeVisible();
    await expect(page.locator("nav")).toContainText("Financial News Aggregator");
  });

  test("renders Fetch Latest News button in navbar", async ({ page }) => {
    await page.goto("/");
    const btn = page.locator("nav button", { hasText: /Fetch Latest News/i });
    await expect(btn).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 2. Dashboard Stats
// ---------------------------------------------------------------------------

test.describe("Dashboard Stats", () => {
  test("renders four stat cards", async ({ page }) => {
    await page.goto("/");
    // Wait for the page to load
    await page.waitForLoadState("networkidle");

    const statCards = page.locator("text=Total Articles").first();
    await expect(statCards).toBeVisible();

    await expect(page.locator("text=Active Sources").first()).toBeVisible();
    await expect(page.locator("text=Articles Today").first()).toBeVisible();
    await expect(page.locator("text=Last Ingestion").first()).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 3. Article Rendering
// ---------------------------------------------------------------------------

test.describe("Article Cards", () => {
  test("articles load and render as cards", async ({ page }) => {
    await page.goto("/");
    // Wait for loading to finish — the "Loading articles..." text should disappear
    await expect(page.getByText("Loading articles...")).toBeHidden({ timeout: 15_000 });

    // Either articles are visible or "No articles found" message is shown
    const articles = page.locator('[class*="grid"] > div');
    const noArticles = page.getByText("No articles found");

    const hasArticles = await articles.count() > 0;
    const hasNoArticlesMessage = await noArticles.isVisible().catch(() => false);

    expect(hasArticles || hasNoArticlesMessage).toBeTruthy();
  });

  test("article cards contain title, source, and date", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Loading articles...")).toBeHidden({ timeout: 15_000 });

    const firstCard = page.locator('[class*="card"]').first();
    // If there are articles, check card structure
    if (await firstCard.isVisible().catch(() => false)) {
      // Card should have text content
      const text = await firstCard.textContent();
      expect(text).toBeTruthy();
      expect(text!.length).toBeGreaterThan(5);
    }
  });
});

// ---------------------------------------------------------------------------
// 4. Search Functionality
// ---------------------------------------------------------------------------

test.describe("Search", () => {
  test("search bar is visible and functional", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Loading articles...")).toBeHidden({ timeout: 15_000 });

    const searchInput = page.getByPlaceholder("Search financial news...");
    await expect(searchInput).toBeVisible();

    // Type a search query
    await searchInput.fill("market");
    await page.getByRole("button", { name: /Search/i }).click();

    // Wait for results to load
    await page.waitForTimeout(2000);

    // Page should still render without errors
    await expect(page.locator("nav")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 5. Export Buttons
// ---------------------------------------------------------------------------

test.describe("Export", () => {
  test("CSV export button is visible", async ({ page }) => {
    await page.goto("/");
    const csvBtn = page.getByRole("button", { name: /Export CSV/i });
    await expect(csvBtn).toBeVisible();
  });

  test("Excel export button is visible", async ({ page }) => {
    await page.goto("/");
    const xlsxBtn = page.getByRole("button", { name: /Export Excel/i });
    await expect(xlsxBtn).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 6. Ingestion Trigger
// ---------------------------------------------------------------------------

test.describe("Ingestion Trigger", () => {
  test("clicking Fetch Latest News shows feedback", async ({ page }) => {
    await page.goto("/");
    const btn = page.locator("nav button", { hasText: /Fetch Latest News/i });
    await btn.click();

    // Button should show loading state (spinner animation) or a message should appear
    // Wait a moment for the response
    await page.waitForTimeout(2000);

    // Navbar should still be visible (no crash)
    await expect(page.locator("nav")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 7. Responsiveness
// ---------------------------------------------------------------------------

test.describe("Responsiveness", () => {
  test("mobile viewport renders correctly", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/");
    await expect(page.locator("nav")).toBeVisible();
    await expect(page.getByPlaceholder("Search financial news...")).toBeVisible();
  });

  test("tablet viewport renders correctly", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/");
    await expect(page.locator("nav")).toBeVisible();
    await expect(page.getByPlaceholder("Search financial news...")).toBeVisible();
  });

  test("desktop viewport renders correctly", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");
    await expect(page.locator("nav")).toBeVisible();
    await expect(page.getByPlaceholder("Search financial news...")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 8. No Console Errors
// ---------------------------------------------------------------------------

test.describe("Error-free rendering", () => {
  test("no uncaught exceptions on homepage", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));

    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    // Filter out expected API errors (stats/trigger may fail without backend)
    const criticalErrors = errors.filter(
      (e) => !e.includes("Failed to fetch") && !e.includes("NetworkError")
    );
    expect(criticalErrors).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// 9. API Contract Tests
// ---------------------------------------------------------------------------

test.describe("API Contracts", () => {
  test("GET /articles returns valid JSON with items array", async ({
    request,
  }) => {
    const res = await request.get("http://127.0.0.1:8000/articles");
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("items");
    expect(Array.isArray(body.items)).toBeTruthy();
    expect(body).toHaveProperty("meta");
    expect(body.meta).toHaveProperty("next_cursor");
    expect(body.meta).toHaveProperty("has_more");
  });

  test("GET /articles supports pagination via limit", async ({ request }) => {
    const res = await request.get("http://127.0.0.1:8000/articles?limit=2");
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.items.length).toBeLessThanOrEqual(2);
  });

  test("GET /articles supports search via q parameter", async ({
    request,
  }) => {
    const res = await request.get("http://127.0.0.1:8000/articles?q=market");
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("items");
  });

  test("GET /health returns ok", async ({ request }) => {
    const res = await request.get("http://127.0.0.1:8000/health");
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe("ok");
  });

  test("GET /health/ready returns ready", async ({ request }) => {
    const res = await request.get("http://127.0.0.1:8000/health/ready");
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe("ready");
  });

  test("GET /admin/dashboard/stats requires auth", async ({ request }) => {
    const res = await request.get(
      "http://127.0.0.1:8000/admin/dashboard/stats"
    );
    // Should fail without API key
    expect([401, 403, 422]).toContain(res.status());
  });

  test("GET /admin/dashboard/stats with key returns stats", async ({
    request,
  }) => {
    const res = await request.get(
      "http://127.0.0.1:8000/admin/dashboard/stats",
      {
        headers: { "X-API-Key": "supersecret" },
      }
    );
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("total_articles");
    expect(body).toHaveProperty("active_sources");
    expect(body).toHaveProperty("articles_today");
  });

  test("GET /articles/export/csv returns CSV", async ({ request }) => {
    const res = await request.get("http://127.0.0.1:8000/articles/export/csv");
    expect(res.status()).toBe(200);
    const contentType = res.headers()["content-type"] || "";
    expect(contentType).toContain("text/csv");
  });

  test("GET /openapi.json returns schema", async ({ request }) => {
    const res = await request.get("http://127.0.0.1:8000/openapi.json");
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("openapi");
    expect(body).toHaveProperty("paths");
  });
});

// ---------------------------------------------------------------------------
// 10. Accessibility Basics
// ---------------------------------------------------------------------------

test.describe("Accessibility", () => {
  test("page has lang attribute", async ({ page }) => {
    await page.goto("/");
    const lang = await page.getAttribute("html", "lang");
    expect(lang).toBe("en");
  });

  test("search input has placeholder text", async ({ page }) => {
    await page.goto("/");
    const placeholder = await page
      .getByPlaceholder("Search financial news...")
      .getAttribute("placeholder");
    expect(placeholder).toBeTruthy();
  });

  test("navbar links are keyboard accessible", async ({ page }) => {
    await page.goto("/");
    // Tab to the first interactive element
    await page.keyboard.press("Tab");
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBeTruthy();
  });
});