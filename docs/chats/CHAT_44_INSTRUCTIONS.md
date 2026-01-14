# Chat #44 — Filters UI

> **Phase:** 5 — General Filters  
> **Previous:** #43 Filters Integration ✅  
> **Next:** #45 Preset Optimizer Core

---

## 🎯 GOAL

Create React UI components for filter configuration:
- Filter settings section in bot configuration
- Category grouping (Time/Volatility/Trend/Portfolio/Protection)
- Filter toggle switches with parameters
- Preview filter effect (optional)
- Filter profiles selector (Conservative/Balanced/Aggressive)
- Filter statistics display

---

## 📋 TASKS

- [ ] `FilterSettings.jsx` — Main filter settings component
- [ ] `FilterCategory.jsx` — Category grouping component
- [ ] `FilterCard.jsx` — Individual filter card with toggle
- [ ] `FilterParams.jsx` — Dynamic parameter inputs
- [ ] `FilterProfileSelector.jsx` — Profile dropdown
- [ ] `FilterStats.jsx` — Statistics display

### FilterSettings Component
```jsx
// Main component for filter configuration
function FilterSettings({ botId }) {
  // Load filters from API
  // Group by category
  // Handle enable/disable
  // Save configuration
}
```

### FilterCategory Component
```jsx
// Collapsible category with filters
function FilterCategory({ name, filters, onToggle, onUpdate }) {
  // Category header with expand/collapse
  // List of FilterCard components
}
```

### FilterCard Component
```jsx
// Individual filter with toggle and params
function FilterCard({ filter, config, onToggle, onUpdate }) {
  // Filter name and description
  // Enable/disable toggle
  // Expandable params section
}
```

### API Integration
```javascript
// api.js additions
export const filterApi = {
  getAvailable: () => fetch('/api/filters/available'),
  getCategories: () => fetch('/api/filters/categories'),
  getProfiles: () => fetch('/api/filters/profiles'),
  getBotConfig: (botId) => fetch(`/api/filters/bot/${botId}`),
  saveBotConfig: (botId, config) => fetch(`/api/filters/bot/${botId}`, {
    method: 'POST',
    body: JSON.stringify(config)
  }),
  applyProfile: (botId, profile) => fetch(`/api/filters/bot/${botId}/profile/${profile}`, {
    method: 'POST'
  }),
  getStats: (botId) => fetch(`/api/filters/bot/${botId}/stats`),
}
```

- [ ] Update `api.js` with filter endpoints
- [ ] Add filter routes to main.py
- [ ] Style with TailwindCSS
- [ ] Test all components

---

## 📁 FILES

```
frontend/src/
├── components/
│   └── Filters/
│       ├── index.js
│       ├── FilterSettings.jsx
│       ├── FilterCategory.jsx
│       ├── FilterCard.jsx
│       ├── FilterParams.jsx
│       ├── FilterProfileSelector.jsx
│       └── FilterStats.jsx
├── pages/
│   └── Bots.jsx               # Update to include filters
└── api.js                      # Add filter API

backend/app/
└── main.py                     # Add filter_routes
```

---

## 📝 GIT COMMIT

```
feat: Add filter configuration UI

- Add FilterSettings component for bot filter config
- Add FilterCategory for grouped display
- Add FilterCard with toggle and params
- Add FilterProfileSelector dropdown
- Add FilterStats display
- Add filter API to frontend
- Integrate filter_routes in main.py

Chat #44: Filters UI
```

---

**Next chat:** #45 — Preset Optimizer Core
