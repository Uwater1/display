Below is a **comprehensive, implementation-ready plan** to build a GitHub Pages site that:

* Reads many `.svg` files from `data/chart/`
* Displays **filename (title) + SVG image below**
* Supports **pagination / next-item navigation**
* Allows navigation by:

  * Clicking a **button on the both side**
  * Pressing the **`A (for previous one), D (for next one)` key** on the keyboard
* Is simple, robust, and compatible with GitHub Pages’ constraints

This is written as a **technical execution plan** suitable to hand directly to a coding agent.

---

## 0. Key Constraints (GitHub Pages Reality Check)

Before designing anything, the agent **must respect these constraints**:

1. **No server-side code**

   * GitHub Pages serves static files only
   * No filesystem access at runtime
2. **No directory listing**

   * Browsers cannot list `data/chart/` automatically
3. **All SVG filenames must be known at build time**

**Implication:**
We must **pre-generate an index of SVG files** (JSON or JS) that the frontend consumes.

---

## 1. Recommended Architecture (High-Level)

```
repo/
├─ data/
│  └─ chart/
│     ├─ chart_001.svg
│     ├─ chart_002.svg
│     └─ ...
├─ public/
│  ├─ index.html
│  ├─ styles.css
│  ├─ app.js
│  └─ charts.json   ← auto-generated
├─ scripts/
│  └─ generate_charts_index.py (or .js)
├─ .github/
│  └─ workflows/
│     └─ pages.yml
└─ README.md
```

---

## 2. SVG Index Generation (Critical Step)

### Purpose

Create a machine-readable list of all SVGs in `data/chart/`.

### Output Format (`charts.json`)

```json
{
  "charts": [
    "chart_001.svg",
    "chart_002.svg",
    "chart_003.svg"
  ]
}
```

### Generation Method

Choose **one**:

#### Option A — Python (Recommended)

* Script scans `data/chart/*.svg`
* Sort filenames (alphabetically or numerically)
* Writes `public/charts.json`

#### Option B — Node.js

* Same logic using `fs.readdirSync`

### When It Runs

* **Locally** before committing
* OR **automatically via GitHub Actions** on push

> This step is mandatory. No workaround exists on static hosting.

---

## 3. GitHub Pages Setup

### Pages Source

* Use **GitHub Actions** (recommended)
* OR `/docs` or `/public` folder

### Workflow Logic

1. Checkout repo
2. Run SVG index generation script
3. Copy assets into `/public`
4. Deploy `/public` to GitHub Pages

> This guarantees charts.json is always up to date.

---

## 4. Frontend Page Structure

### index.html Responsibilities

* Mount a single-page app (SPA-style)
* Load `charts.json`
* Display:

  * SVG filename as title
  * SVG image
* Provide navigation UI

### Minimal DOM Structure

```html
<body>
  <div id="app">
    <div id="title"></div>
    <div id="viewer">
      <img id="svg-image" />
    </div>
    <button id="next-btn">▶</button>
  </div>
</body>
```

---

## 5. Rendering Logic (app.js)

### State Variables

* `charts[]` — list from JSON
* `currentIndex` — integer
* Optional: URL-based state (`?i=42`)

### Load Flow

1. `fetch('charts.json')`
2. Store list
3. Render first SVG

### Render Function

* Set title: filename
* Set `<img src="data/chart/<filename>">`
* Ensure SVG scales responsively

---

## 6. Navigation Logic

### Button Navigation

* Right-side floating button
* `onclick → nextChart()`

### Keyboard Navigation

* Global key listener
* `keydown`
* If key === `'d'` or `'D'` → next
* (Optional) `'a'` → previous

### Wraparound Behavior

* When last SVG reached:

  * Loop back to first
  * OR disable button (design choice)

---

## 7. Scrolling / Paging Behavior

### Interpretation of “scroll to next page”

Best UX for SVG galleries:

#### Recommended: **One Chart Per View**

* Clicking next:

  * Replaces SVG content
  * Scrolls viewport to top
* Avoid vertical infinite scroll (SVGs vary in size)

### Optional Enhancements

* CSS `scroll-behavior: smooth`
* Fade/slide animation between charts

---

## 8. CSS Layout Plan

### Goals

* Center SVG
* Responsive scaling
* Fixed navigation button on right

### Key CSS Concepts

* `max-width: 100vw; max-height: 90vh`
* `object-fit: contain`
* Fixed-position button:

  ```css
  position: fixed;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  ```

---

## 9. URL State (Optional but Strongly Recommended)

### Why

* Shareable links
* Refresh-safe navigation

### Implementation

* Use query param: `?i=12`
* On load:

  * Parse index
  * Clamp to valid range
* On navigation:

  * Update `history.pushState`

---

## 10. Accessibility & UX Considerations

* Button has:

  * `aria-label="Next chart"`
* Keyboard navigation documented on page
* Disable text selection
* Prevent page scroll on keypress if desired

---

## 11. Performance Considerations

* SVGs are loaded **on demand**
* Browser caches SVGs automatically
* No preloading needed unless SVGs are tiny

Optional:

* Preload next SVG after render

---

## 12. Development Checklist (For Coding Agent)

### Mandatory

* [ ] SVG index generator
* [ ] charts.json committed or generated in CI
* [ ] Fetch + render logic
* [ ] Button navigation
* [ ] Keyboard `D` navigation
* [ ] GitHub Pages deployment

### Optional Enhancements

* [ ] Previous (`A`) key
* [ ] URL state
* [ ] Animation
* [ ] Dark mode

---

## 13. Common Pitfalls (Warn the Agent)

1. ❌ Trying to list directory contents in JS
2. ❌ Assuming GitHub Pages supports backend logic
3. ❌ Forgetting relative paths break on Pages
4. ❌ Hardcoding SVG list manually

---

## 14. Minimal Tech Stack Summary

* **HTML**: single page
* **CSS**: layout + button
* **Vanilla JS**: state + navigation
* **GitHub Actions**: build + deploy
* **No frameworks required**

---

If you want, next steps could be:

* Produce a **task-by-task coding prompt** for the agent
* Design a **file-by-file responsibility spec**
* Provide a **fallback plan** if SVG count exceeds 10k

Just say which one.
