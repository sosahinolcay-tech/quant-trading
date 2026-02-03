# Frontend Redesign Master Prompt (OpenBB-Style)

## Role & Goal
You are a senior product designer and principal frontend engineer redesigning a professional quantitative finance platform (similar to OpenBB).
The goal is Dribbble-level visual polish combined with elite functional UX for power users.

This is not a landing page. This is a daily-use trading/analytics tool where speed, clarity, and density matter.

## Core Constraints
- Tech stack: React + TypeScript
- Styling: Tailwind CSS
- State: lightweight (Zustand or React Context)
- Charts: Recharts or D3
- Must be modular, scalable, and production-ready
- No fake placeholder UI logic — all components must be functional

## Design Language (VERY IMPORTANT)
Visual inspiration: Dribbble, Linear, Stripe Dashboard, Vercel, Arc Browser

Style keywords:
- Dark-mode first
- Soft glassmorphism (used sparingly)
- Subtle gradients (no neon)
- Clean typography (Inter / Geist / SF-like)
- Rounded corners (8–12px)
- Smooth micro-interactions
- High information density without clutter

Avoid “pretty but useless” UI. Every visual element must serve functionality.

## UX Principles
- Keyboard-first navigation (Cmd+K command palette)
- Resizable panels
- Dockable widgets
- Collapsible sidebars
- Tooltips on hover (financial context aware)
- Loading skeletons instead of spinners
- Zero unnecessary animations

## Application Layout
Design and implement:

### 1) Global Layout
Top navigation bar:
- App name
- Global search
- Market status indicator (open/closed)
- Theme toggle

Left sidebar:
- Dashboards
- Screener
- Charts
- Strategies
- Portfolio
- Settings

Main workspace:
- Tab-based multi-view system
- Each tab holds a dashboard or chart

### 2) Dashboard System
Grid-based layout

Widgets:
- Market overview
- Heatmap
- OHLC chart
- Volume profile
- News feed

Widgets must be:
- Resizable
- Rearrangeable
- Persist layout state

### 3) Charting Experience
- Professional trading chart look
- Crosshair
- Zoom & pan
- Multiple indicators (MA, RSI, MACD)
- Tooltips with real data formatting

## Implementation Requirements
Provide:
- Component folder structure
- Reusable UI primitives (Button, Card, Modal)
- One fully implemented dashboard page
- One fully implemented chart page
- Use realistic mock financial data (no lorem ipsum)
- Comment code only where non-obvious

## Output Format
- Brief design rationale
- Folder structure
- Key UI components
- Example pages (code)

## Final Check
Before outputting code, verify:
- This would impress a Dribbble designer
- This would satisfy a professional trader
- This would pass a senior frontend code review

If any of the above fail, revise before answering.
