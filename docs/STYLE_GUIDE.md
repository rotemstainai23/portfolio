# STYLE_GUIDE.md

This document defines UI and styling conventions for the portfolio system.

Primary objective:

Maintain visual consistency.

Do not invent new design systems.

Follow existing architecture.

---

# Core Design Rules

Use:

```text
templates/_shared.css
```

as the single source of truth (SSOT) for styling.

Do not introduce competing design systems.

Do not invent new design tokens.

If additional styling is needed:

Prefer extending existing tokens and patterns.

Reference:

```text
~/CLAUDE MEMORY/Shared/design-tokens.md
```

---

# Language Rules

## Hebrew Reports

All report pages must use:

```html
<html lang="he" dir="rtl">
```

Requirements:

- RTL layout
- Hebrew-first typography
- Proper alignment for RTL spacing

Used in:

```text
templates/*.html
analyses/<TICKER>/*
```

---

## Main Dashboard

`portfolio.html` remains:

```html
<html lang="en">
```

Reason:

General-purpose dashboard UI.

Do not convert to RTL unless explicitly requested.

---

# Typography

Preferred font:

```text
Heebo
```

Use Heebo for:

- Reports
- Analysis pages
- Hebrew UI work

Maintain consistency.

Avoid introducing random font systems.

---

# Visualizations

Must work:

```text
offline
```

No external dependencies.

Preferred approaches:

## CSS-native charts

Use:

- `conic-gradient`
- CSS bars
- CSS progress components
- lightweight HTML/CSS visualizations

Examples:

```text
Donut charts
Bar charts
Risk meters
Allocation visuals
```

---

# Forbidden Libraries

Do NOT introduce:

```text
Chart.js
```

Avoid:

- heavy charting libraries
- CDN dependencies
- JavaScript visualization frameworks

Reason:

System is intentionally dependency-free.

---

# Frontend Philosophy

Keep UI:

- lightweight
- readable
- fast
- dependency-free

Prefer:

Minimal JavaScript.

Avoid unnecessary frameworks.

---

# Design Consistency

New pages should visually align with:

```text
portfolio.html
```

and:

```text
templates/_shared.css
```

Before creating new visual patterns:

Check existing styles first.

Prefer reusing.

Do not redesign working UI unnecessarily.

---

# Component Rules

Prefer:

- reusable CSS classes
- shared spacing
- shared typography
- consistent card styling

Avoid:

- inline CSS sprawl
- duplicated styling systems
- random spacing conventions

---

# Change Philosophy

When editing UI:

Prefer:

small, surgical improvements.

Do NOT rewrite working layouts without strong reason.

Priority order:

1. Correctness
2. Consistency
3. Readability
4. Maintainability
5. Aesthetics