# Chat #36 — Score UI

> **Phase:** 4 — Signal Score  
> **Previous:** #35 Score Multi-TF ✅  
> **Next:** #37 Filters Architecture

---

## 🎯 GOAL

Create UI components for displaying signal scores in the frontend - badges, tooltips, filters, and visualizations.

---

## 📋 TASKS

- [ ] Create `ScoreBadge.jsx` component with grade color coding
- [ ] Add tooltip with score breakdown (4 components)
- [ ] Update `TradesTable.jsx` with score column and filter
- [ ] Add filter by grade (A-F checkboxes)
- [ ] Create score distribution chart
- [ ] Add score column sorting
- [ ] Mobile responsive design
- [ ] Integration with existing Indicator page

---

## 📐 COMPONENT SPECIFICATION

### ScoreBadge Component

```jsx
<ScoreBadge 
  score={85} 
  grade="A"
  showTooltip={true}
  size="md"  // sm | md | lg
/>
```

Features:
- Color-coded background by grade
- Hover tooltip with breakdown
- Click to expand details
- Compact and full modes

### Grade Colors

| Grade | Background | Text |
|-------|------------|------|
| A | #22c55e (green) | white |
| B | #84cc16 (lime) | white |
| C | #eab308 (yellow) | black |
| D | #f97316 (orange) | white |
| F | #ef4444 (red) | white |

### TradesTable Updates

- New column: "Score" with ScoreBadge
- Filter dropdown: All / A / B / C / D / F
- Sort by score (asc/desc)
- Score distribution summary in header

### Score Distribution Chart

- Bar chart showing count by grade
- Click on bar to filter table
- Mini sparkline version for compact view

---

## 📁 FILES

```
frontend/src/components/Indicator/
├── ScoreBadge.jsx           # NEW: Score display component
├── ScoreTooltip.jsx         # NEW: Breakdown tooltip
├── ScoreDistribution.jsx    # NEW: Distribution chart
├── TradesTable.jsx          # UPDATE: Add score column
└── index.js                 # UPDATE: Export new components

frontend/src/pages/
└── Indicator.jsx            # UPDATE: Integration
```

---

## 🔌 API INTEGRATION

Uses existing endpoints from Chat #35:
- `GET /api/signal-score/grades` — Get grade info
- `GET /api/signal-score/calculate` — Calculate single score
- `POST /api/signal-score/batch` — Batch score trades

---

## 📝 GIT COMMIT

```
feat: add Signal Score UI components

- Create ScoreBadge component with grade colors
- Add tooltip with score breakdown
- Update TradesTable with score column and filter
- Add score distribution visualization
- Mobile responsive design

Chat #36: Score UI
```

---

**Next chat:** #37 — Filters Architecture
