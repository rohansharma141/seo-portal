# SEO Strategy — Claude Code Reference Document
# Source: Google Search Central Official Documentation (May 2026)
# Apply this document to every website and page build.

---

## DOCUMENT PURPOSE

This is a machine-readable SEO strategy baseline. Feed it to Claude Code at the start of every website or page build. It contains implementation rules, technical requirements, content standards, and structured data templates derived directly from Google's official SEO Fundamentals documentation.

---

## 1. HOW GOOGLE SEARCH WORKS (The Pipeline)

Google processes every page through 3 stages. Failure at any stage means no ranking.

```
CRAWL → INDEX → SERVE
```

### Stage 1: Crawl
- Googlebot discovers pages via links, sitemaps, and redirects
- Renders pages using a recent version of Chrome (JavaScript is executed)
- Crawl is NOT guaranteed even if page is accessible
- Common crawl blockers: robots.txt disallow, server errors, login walls, infinite scroll without pagination

### Stage 2: Index
- Google parses text, images, video; processes `<title>`, alt attributes, headings
- Chooses one canonical URL per piece of content from duplicate clusters
- Stores signals: language, country, usability, page experience
- Index is NOT guaranteed even if crawled
- Common index blockers: low quality content, `noindex` meta tag, JS-rendered content not accessible to Googlebot

### Stage 3: Serve (Rank)
- Hundreds of ranking signals evaluated per query
- Relevance determined by user location, language, device, query intent
- Being indexed does NOT guarantee appearing in results
- Common serve failures: content irrelevant to query, low quality vs competitors

### DEVELOPER ACTION CHECKLIST (per page)
```
[ ] Page is publicly accessible (no login wall, not blocked by robots.txt)
[ ] robots.txt verified: no unintentional disallows on important pages
[ ] noindex tag NOT present on pages that should be indexed
[ ] JavaScript content renders correctly (use URL Inspection Tool to verify)
[ ] Server returns correct HTTP status codes (200 for live, 301 for moved, 404 for removed)
[ ] Page loads on mobile (mobile-first indexing is default)
[ ] Page served over HTTPS
[ ] Google Search Console verified and sitemap submitted
```

---

## 2. TECHNICAL SEO REQUIREMENTS

### 2.1 URL Structure
```
GOOD: /projects/godrej-samaris-sector-53-gurgaon
BAD:  /p?id=2847364

RULES:
- Use descriptive, human-readable words in URLs
- Separate words with hyphens, not underscores
- Group related pages in directories: /projects/, /blog/, /developers/
- Each directory signals crawl frequency — stable content in /about/, fast-changing in /projects/
- Lowercase only
- No special characters except hyphens
```

### 2.2 Crawlability
```
robots.txt rules:
- Use Disallow to BLOCK crawling (e.g. /dashboard/, /admin/, /api/)
- Do NOT use robots.txt to prevent indexing — use noindex meta tag instead
- Block state-changing URLs (login, checkout, add-to-cart, comment submission)
- Submit sitemap URL in robots.txt: Sitemap: https://example.com/sitemap.xml

Sitemaps:
- Required for sites with dynamic or frequently updated content
- Include all URLs you want indexed
- Prioritize recently updated pages for crawl budget management
- Submit via Google Search Console
- Use image sitemaps for image-heavy sites (real estate property photos)
- Update sitemap when new pages are published

Crawlable links:
- Use standard <a href=""> tags only — NOT onclick handlers, NOT JavaScript navigation
- Every page must be reachable from at least one other crawlable link
- Multi-page articles need visible prev/next navigation links
- Infinite scroll requires a paginated fallback version
```

### 2.3 Canonicalization
```
Problem: Same content accessible at multiple URLs wastes crawl budget and splits ranking signals.

Solution — in order of preference:
1. 301 redirect non-preferred URLs to the canonical
2. <link rel="canonical" href="https://example.com/preferred-url" /> in <head>
3. Google will auto-detect in simple cases, but explicit is better

When to apply:
- www vs non-www versions
- HTTP vs HTTPS (should be 301 redirected anyway)
- Trailing slash vs no trailing slash
- URL parameters that don't change content (?sort=price, ?ref=banner)
- Broker landing pages generated from the same template (PropOS: each must have UNIQUE content)
```

### 2.4 JavaScript SEO (Critical for Next.js)
```
ISSUE: Client-side rendered content may not be indexed correctly.

REQUIREMENTS for Next.js / React apps:
- Use SSR (Server Side Rendering) or SSG (Static Site Generation) for all public pages
- Critical content must be in the initial HTML response, not injected post-load
- Test with: Google Search Console → URL Inspection → View Crawled Page
- Do NOT rely on client-side rendering for: titles, meta descriptions, headings, main body content, structured data

VERIFY:
- Run URL Inspection Tool on 5 key pages
- Rendered HTML should match what users see
- No blank content sections visible in the crawled screenshot
```

### 2.5 Page Experience (Core Web Vitals)
```
Google ranking signal. Measure at: https://pagespeed.web.dev

Key metrics:
- LCP (Largest Contentful Paint): target < 2.5s — main image/heading loads fast
- CLS (Cumulative Layout Shift): target < 0.1 — no unexpected layout jumps
- INP (Interaction to Next Paint): target < 200ms — UI responds quickly to clicks

Common issues on real estate sites:
- Large unoptimized property photos → compress to WebP, use lazy loading, set explicit dimensions
- No explicit width/height on images → causes CLS
- Heavy third-party scripts → load async or defer

DO NOT use:
- Intrusive interstitials that cover content on mobile
- Pop-ups that appear immediately (before user has read content)
- Sticky banners that take up more than 20% of screen
```

### 2.6 HTTPS
```
- All sites MUST serve over HTTPS
- 301 redirect all HTTP to HTTPS
- Ensure all resources (images, CSS, JS) are served over HTTPS (no mixed content)
- HTTPS is a confirmed (though minor) ranking signal
```

---

## 3. ON-PAGE IMPLEMENTATION

### 3.1 Title Tags
```html
<!-- Rules -->
<!-- - Unique per page (NO duplicate titles across the site) -->
<!-- - 50–60 characters optimal (Google truncates at ~600px) -->
<!-- - Most important keyword toward the front -->
<!-- - Include brand name at end after pipe or dash -->
<!-- - Accurately describe page content — no clickbait -->

<!-- GOOD examples for Kedar Estate -->
<title>Godrej Samaris Sector 53 Gurgaon — 3BHK Luxury Apartments | Kedar Estate</title>
<title>Luxury Resale Flats in Golf Course Road Gurgaon | Kedar Estate</title>

<!-- GOOD examples for PropOS -->
<title>PropOS — AI Property Operating System for Indian Real Estate Brokers</title>
<title>Prithvi AI WhatsApp Bot for Real Estate Brokers | PropOS</title>

<!-- BAD -->
<title>Home</title>
<title>Page 1</title>
<title>Untitled</title>
```

### 3.2 Meta Descriptions
```html
<!-- Rules -->
<!-- - Unique per page -->
<!-- - 120–160 characters -->
<!-- - Summarize page content in a way that makes users want to click -->
<!-- - NOT a ranking factor, but affects click-through rate -->
<!-- - Google may override with content from the page body -->

<meta name="description" content="First-hand review of Godrej Samaris at Sector 53, Gurgaon. 3BHK luxury apartments starting ₹3.2Cr. Direct developer pricing, OC received. Site visit insights from Kedar Estate.">
```

### 3.3 Heading Structure
```html
<!-- ONE <h1> per page — main topic only -->
<!-- H2 for major sections -->
<!-- H3 for sub-sections -->
<!-- Order doesn't need to be perfect, but logical structure helps users and accessibility -->

<!-- GOOD structure for a project page -->
<h1>Godrej Samaris Sector 53 Gurgaon — Honest Review</h1>
  <h2>Project Overview</h2>
  <h2>What I Found on My Site Visit</h2>
    <h3>Construction Quality</h3>
    <h3>Location Advantages</h3>
  <h2>Pricing Analysis</h2>
  <h2>My Recommendation</h2>
```

### 3.4 Images
```html
<!-- Every image needs descriptive alt text -->
<!-- Alt text: describe what the image shows, not the filename -->
<!-- Near images: place them close to relevant body text -->

<!-- GOOD -->
<img 
  src="/images/godrej-samaris-lobby.webp" 
  alt="Grand entrance lobby of Godrej Samaris with marble flooring and double-height ceiling"
  width="800" 
  height="600"
  loading="lazy"
/>

<!-- BAD -->
<img src="/img/img001.jpg" alt="image" />
<img src="/img/photo.jpg" alt="" />

<!-- Requirements -->
<!-- - Set explicit width and height to prevent CLS -->
<!-- - Use WebP format for smaller file sizes -->
<!-- - Lazy load images below the fold -->
<!-- - First above-fold image: do NOT lazy load (use loading="eager") -->
<!-- - Filename should be descriptive: godrej-samaris-lobby.webp not img001.webp -->
```

### 3.5 Internal Linking
```html
<!-- Link to related pages within your site -->
<!-- Use descriptive anchor text — NOT "click here" or "read more" -->

<!-- GOOD -->
<a href="/projects/dlf-camellias-review">Read our DLF Camellias review</a>
<a href="/blog/golf-course-road-market-analysis">Golf Course Road market analysis 2026</a>

<!-- BAD -->
<a href="/page2">click here</a>
<a href="/dlf">this</a>

<!-- Add nofollow or noopener to external links you don't control -->
<a href="https://externalsite.com" rel="nofollow noopener">External Resource</a>
```

---

## 4. CONTENT STANDARDS

### 4.1 The Non-Commodity Test
```
Every piece of content must pass this test before publishing:

COMMODITY (DO NOT PUBLISH AS-IS):
- "Top 5 things to check before buying a flat"
- "7 tips for first-time homebuyers"
- "Benefits of investing in Gurgaon real estate"
→ This content could be written by anyone with a Google search. Provides no unique value.

NON-COMMODITY (TARGET THIS):
- "Why I advised my client to skip the inspection at [Project] and save ₹2L — and why I'd do it again"
- "I visited Godrej Samaris 3 times. Here's what changed each visit and what the brochure hides"
- "Golf Course Road vs Golf Course Extension: what our last 8 closures tell us"
→ Requires real experience, real data, real judgment. Cannot be replicated by AI or generic writers.
```

### 4.2 The "Who, How, Why" Check
```
Before publishing any page, verify:

WHO:
[ ] Is there a named author/byline visible on the page?
[ ] Does the byline link to an author page with background information?
[ ] Is the author's relevant experience stated?

HOW:
[ ] Does the content show evidence of real work? (site visits, data, photos, transactions)
[ ] If AI-assisted, is the process disclosed where it matters?
[ ] Are claims supported by specific details, not generalities?

WHY:
[ ] Is this content primarily for the reader's benefit?
[ ] Would this reader bookmark or share this page?
[ ] Would this appear in a reputable publication?
[ ] Would a reader need to search again after reading this? (If yes: rewrite)
```

### 4.3 E-E-A-T Implementation
```
E = Experience: Show first-hand involvement
  → Real site visit photos with observations
  → Specific transaction examples (anonymized where needed)
  → Personal recommendations with stated reasoning

E = Expertise: Demonstrate knowledge depth
  → Author bio with 25+ years combined broker experience
  → Specific project knowledge (RERA numbers, developer track record, micro-market data)
  → Cross-references to actual deals closed

A = Authoritativeness: Build recognition
  → Consistent publishing on specific topics (Golf Course Road micro-market)
  → Get listed/mentioned on reputable real estate sites
  → Link out to credible sources (RERA portal, builder official sites)

T = Trust (most important):
  → Accurate information — no fake urgency, no inflated claims
  → Clear contact information
  → Physical address on site (for local business)
  → Privacy policy and terms visible
  → No pop-up spam or deceptive UX patterns
```

### 4.4 Content Freshness
```
[ ] Review and update old pages every 6 months
[ ] Do NOT change dates without substantially updating content (Google penalizes fake freshness)
[ ] Delete or redirect pages with no search traffic and no value after 12 months
[ ] Mark content with accurate publication and last-updated dates
```

---

## 5. STRUCTURED DATA (Schema.org)

### 5.1 Local Business — Kedar Estate
```json
{
  "@context": "https://schema.org",
  "@type": "RealEstateAgent",
  "name": "Kedar Estate and Investments",
  "description": "Delhi NCR luxury real estate brokerage specializing in HNI and NRI property transactions",
  "url": "https://kedar.estate",
  "telephone": "+91-XXXXXXXXXX",
  "email": "contact@kedar.estate",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[Street Address]",
    "addressLocality": "Gurgaon",
    "addressRegion": "Haryana",
    "postalCode": "122002",
    "addressCountry": "IN"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 28.4595,
    "longitude": 77.0266
  },
  "areaServed": ["Gurgaon", "Delhi", "Noida", "Delhi NCR"],
  "priceRange": "₹₹₹₹",
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
    "opens": "09:00",
    "closes": "19:00"
  },
  "sameAs": [
    "https://www.99acres.com/[profile-url]",
    "https://www.linkedin.com/company/[company]"
  ]
}
```

### 5.2 Software Application — PropOS
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "PropOS",
  "alternateName": "Property Operating System",
  "description": "AI-powered property operating system for Indian real estate brokers, featuring Prithvi AI assistant for WhatsApp lead management",
  "url": "https://propos.in",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web, WhatsApp",
  "offers": {
    "@type": "Offer",
    "price": "[monthly price]",
    "priceCurrency": "INR",
    "priceSpecification": {
      "@type": "UnitPriceSpecification",
      "billingDuration": "P1M"
    }
  },
  "featureList": [
    "AI landing page generator",
    "WhatsApp AI agent (Prithvi)",
    "Lead management dashboard",
    "Broker website builder"
  ],
  "creator": {
    "@type": "Person",
    "name": "Rohan [Last Name]",
    "jobTitle": "Founder"
  }
}
```

### 5.3 Real Estate Listing — Property Pages
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Godrej Samaris 3BHK — Sector 53 Gurgaon",
  "description": "Luxury 3BHK apartment in Godrej Samaris, Sector 53 Golf Course Road Gurgaon",
  "image": [
    "https://example.com/images/godrej-samaris-front.webp",
    "https://example.com/images/godrej-samaris-lobby.webp"
  ],
  "offers": {
    "@type": "Offer",
    "price": "32000000",
    "priceCurrency": "INR",
    "availability": "https://schema.org/InStock"
  },
  "brand": {
    "@type": "Brand",
    "name": "Godrej Properties"
  }
}
```

### 5.4 Article — Blog / Review Pages
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Godrej Samaris Sector 53 Review: What I Found After 3 Site Visits",
  "author": {
    "@type": "Person",
    "name": "Rohan [Last Name]",
    "url": "https://kedar.estate/team/rohan"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Kedar Estate and Investments",
    "logo": {
      "@type": "ImageObject",
      "url": "https://kedar.estate/logo.png"
    }
  },
  "datePublished": "2026-05-16",
  "dateModified": "2026-05-16",
  "image": "https://kedar.estate/images/godrej-samaris-hero.webp",
  "description": "First-hand review of Godrej Samaris after multiple site visits"
}
```

### 5.5 FAQ — For Common Questions Pages
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Is Godrej Samaris a good investment in 2026?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[Genuine, detailed answer based on real market knowledge]"
      }
    }
  ]
}
```

### 5.6 Implementation Rules for Structured Data
```
[ ] Add JSON-LD in <script type="application/ld+json"> in <head> or before </body>
[ ] Test every page with: https://search.google.com/test/rich-results
[ ] Do NOT mark up content not visible on the page
[ ] Do NOT add fake reviews or misleading data
[ ] One primary schema type per page (can have secondary supporting types)
[ ] Validate that schema matches visible page content exactly
```

---

## 6. SITE-SPECIFIC RULES

### 6.1 Kedar Estate Website
```
Domain: kedar.estate (or equivalent)
Site type: Local business + content/review site

URL structure:
/                          — Homepage (brand, trust, contact)
/projects/                 — All projects index
/projects/[project-slug]/  — Individual project pages (unique content per project)
/blog/                     — Market analysis, insights
/blog/[article-slug]/      — Individual articles
/team/                     — About/team page with bios
/contact/                  — Contact + Google Maps embed

Content requirements per project page:
- H1: [Project Name] + [Location] + one differentiating phrase
- 600+ words minimum, all original, first-hand
- At least 5 real photos with descriptive alt text
- Named author + date published + date updated
- Specific price data (actual, not "on request")
- RERA registration number if available
- Honest pros AND cons (builds trust)
- Internal links to related projects and blog posts

Technical requirements:
- Google Business Profile: MUST be set up and fully completed
- LocalBusiness schema on homepage and contact page
- Product/RealEstate schema on each project page
- XML sitemap with image sitemap extension
- robots.txt: allow all project and blog pages, block /admin
- Google Search Console: verified, sitemap submitted

DO NOT:
- Duplicate project descriptions from developer brochures (scraped content penalty)
- Show prices as "on request" — publish real ranges
- Use intrusive lead-capture popups on first page load
```

### 6.2 PropOS Marketing Website
```
Domain: propos.in (or equivalent)
Site type: SaaS product site

URL structure:
/                          — Homepage (product overview, value prop)
/features/                 — Features index
/features/[feature-slug]/  — Individual feature pages
/pricing/                  — Pricing page
/blog/                     — Content marketing for brokers
/blog/[article-slug]/      — Articles
/case-studies/             — Real broker success stories (once available)

Content requirements:
- Homepage H1: Specific, not generic ("AI Operating System for Indian Real Estate Brokers")
- Every feature page: explain what it does + who it's for + real example
- Blog content: Target broker pain points (lead management, WhatsApp, site visits, closures)
- Author byline on all blog posts: Rohan's name + dual credential (broker + builder)

Technical requirements:
- Next.js SSR/SSG for all public pages (CRITICAL — client-side rendering = indexing failure)
- SoftwareApplication schema on homepage
- robots.txt: Disallow /dashboard/, /api/, /admin/, /app/
- Canonical tags on all pages (especially if broker pages share template structure)
- Core Web Vitals: LCP < 2.5s (test on mobile 3G)

CRITICAL for PropOS broker landing pages:
- Each broker's generated page MUST have unique content — not duplicated boilerplate
- Prithvi AI must generate distinct descriptions per broker/project combination
- If two brokers list the same project, their pages must differ substantively
- Implement canonical pointing to primary broker page if exact duplicates exist
- Each broker page needs: unique title, unique meta description, unique H1
```

### 6.3 Broker Websites (Generated by PropOS)
```
These are the landing pages PropOS generates for individual brokers.

URL structure: [broker-domain].com or [propos-subdomain]/[broker-slug]

Required per page:
- Unique H1 incorporating: broker name / brand + project name + location
- 200+ words of original content (not scraped from developer site)
- At least 3 real photos with alt text (broker uploads or site visit)
- Broker contact info (phone, WhatsApp, email)
- RealEstateAgent + Product schema

Technical:
- Canonical tag pointing to the authoritative URL
- robots.txt: allow all broker-facing pages, block /leads/, /crm/
- Mobile-first (WhatsApp users arrive on mobile)
- Fast load: < 3s on 4G (Indian mobile network benchmark)
- No intrusive popups (WhatsApp widget is fine, full-page overlays are not)
```

---

## 7. MONITORING AND MAINTENANCE

### 7.1 Search Console — Monthly Checklist
```
[ ] Check Coverage report: any new Excluded or Error pages?
[ ] Check Performance: any queries with high impressions but low CTR? (improve meta descriptions)
[ ] Check Core Web Vitals report: any pages in "Poor" or "Needs Improvement"?
[ ] Check any manual actions or security issues
[ ] Submit newly published URLs for indexing (URL Inspection → Request Indexing)
```

### 7.2 Content Audit — Quarterly
```
[ ] Review all pages with 0 impressions in last 90 days
[ ] Update or redirect/remove low-quality pages
[ ] Refresh outdated content (price updates, project status)
[ ] Check for pages with good impressions but low clicks (CTR < 2%): rewrite title/meta
[ ] Update lastmod dates in sitemap only for pages with real content changes
```

### 7.3 Technical Audit — On Every Deploy
```
[ ] Run Lighthouse on 3 key pages (mobile mode)
[ ] Verify robots.txt is correct (especially after URL structure changes)
[ ] Verify sitemap is up to date and returns 200
[ ] Test Rich Results for structured data pages
[ ] Verify canonical tags on all dynamically generated pages
[ ] Check for broken internal links
[ ] Verify HTTPS is working and no mixed content warnings
```

---

## 8. WHAT NOT TO DO (Confirmed Ineffective by Google)

```
IGNORE THESE — confirmed waste of time by Google documentation:

1. Meta keywords tag — Google does not use it. Never has.
2. llms.txt files — No special treatment from Google AI systems.
3. "Chunking" content for AI — Google already understands full-page context.
4. Exact keyword matching — Google understands synonyms and semantic meaning.
5. Writing to a specific word count — No ideal word count exists.
6. Changing publish dates without updating content — Detected and ignored.
7. Adding content volume to "seem fresh" — Does not help rankings.
8. Inauthentic brand mentions / mention farming — Spam systems detect and discount.
9. Exact-match keywords in domain name — Minimal ranking effect.
10. Subdomains vs subdirectories debate — Pick what works for your business structure.
11. Separate AI-optimized versions of content — Unnecessary; same content standards apply.
12. Schema markup beyond what's visible — Marked up content must match visible page.
```

---

## 9. TOOLS REFERENCE

```
Google Search Console:   https://search.google.com/search-console
Rich Results Test:        https://search.google.com/test/rich-results
URL Inspection Tool:      via Search Console → URL Inspection
PageSpeed Insights:       https://pagespeed.web.dev
Core Web Vitals report:   via Search Console → Experience → Core Web Vitals
Structured Data Guide:    https://developers.google.com/search/docs/appearance/structured-data/search-gallery
Robots.txt Tester:        via Search Console → Settings → Robots.txt
```

---

## 10. QUICK-START CHECKLIST FOR NEW WEBSITE BUILD

```
BEFORE LAUNCH:
[ ] HTTPS configured and redirects working
[ ] robots.txt: allow important pages, block admin/api/app routes
[ ] XML sitemap generated and accessible at /sitemap.xml
[ ] All pages have unique title tags (50–60 chars)
[ ] All pages have unique meta descriptions (120–160 chars)
[ ] All images have descriptive alt text and explicit dimensions
[ ] One H1 per page, logical H2/H3 structure
[ ] Internal links use descriptive anchor text
[ ] Canonical tags implemented (especially on dynamic/generated pages)
[ ] Structured data added (validate with Rich Results Test)
[ ] Google Search Console: site verified, sitemap submitted
[ ] Google Business Profile set up (for local businesses)
[ ] Core Web Vitals: LCP < 2.5s, CLS < 0.1 on mobile
[ ] No intrusive popups or interstitials
[ ] JavaScript content verified via URL Inspection (SSR/SSG confirmed)

FIRST MONTH:
[ ] 5+ original, non-commodity content pages published with author bylines
[ ] Search Console reviewed for crawl errors
[ ] First performance report reviewed (impressions, clicks, average position)
[ ] Rich results confirmed appearing in test tool
```

---

*Document version: 1.0 — May 2026*
*Source: Google Search Central Documentation (all 6 SEO Fundamentals articles)*
*Next review: August 2026*
