# 🎨 UI Components Library

Reusable React components with consistent design system for KOMAS Trading Server.

## 📦 Installation

```jsx
import { Button, Card, Input, Badge, Select, Modal, Tooltip, Spinner, Alert, ThemeToggle } from './components/ui';
```

---

## 🧩 Components

### Button

Versatile button with 7 variants and loading states.

**Variants:** `primary` | `secondary` | `success` | `danger` | `warning` | `ghost` | `outline`  
**Sizes:** `sm` | `md` | `lg`

```jsx
// Basic
<Button variant="primary" size="md">Click me</Button>

// With loading
<Button variant="success" loading={isLoading}>Save</Button>

// With icon
<Button variant="danger" icon={<TrashIcon />}>Delete</Button>

// Full width
<Button fullWidth>Submit</Button>
```

---

### Card

Container component with composable sub-components.

**Variants:** `default` | `bordered` | `elevated` | `glass`

```jsx
<Card variant="elevated">
  <Card.Header>
    <Card.Title>Dashboard</Card.Title>
    <Card.Description>Overview of your trading activity</Card.Description>
  </Card.Header>
  <Card.Body>
    <p>Content goes here</p>
  </Card.Body>
  <Card.Footer>
    <Button>Action</Button>
  </Card.Footer>
</Card>
```

---

### Input

Text input with validation and icons.

```jsx
// Basic
<Input 
  label="Email" 
  type="email"
  placeholder="Enter your email"
/>

// With validation
<Input 
  label="Password"
  type="password"
  error="Password is required"
/>

// With icons
<Input 
  label="Search"
  leftIcon={<SearchIcon />}
  placeholder="Search..."
/>

// With helper text
<Input 
  label="API Key"
  helperText="Keep this secret"
/>
```

---

### Badge

Status indicators and tags.

**Variants:** `primary` | `secondary` | `success` | `danger` | `warning` | `info` | `gray`  
**Sizes:** `sm` | `md` | `lg`

```jsx
// Basic
<Badge variant="success">Active</Badge>

// With dot indicator
<Badge variant="danger" dot>Offline</Badge>

// Different sizes
<Badge variant="info" size="sm">New</Badge>
```

---

### Select

Dropdown select field.

```jsx
<Select
  label="Country"
  options={[
    { value: 'us', label: 'United States' },
    { value: 'uk', label: 'United Kingdom' },
    { value: 'jp', label: 'Japan', disabled: true }
  ]}
  value={selected}
  onChange={(e) => setSelected(e.target.value)}
  placeholder="Select a country..."
/>

// With validation
<Select
  label="Category"
  options={categories}
  error="Please select a category"
/>
```

---

### Modal

Dialog overlay with backdrop.

**Sizes:** `sm` | `md` | `lg` | `xl` | `full`

```jsx
<Modal 
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Confirm Action"
  size="md"
>
  <p>Are you sure you want to delete this item?</p>
  <div className="flex gap-2 mt-4">
    <Button variant="secondary" onClick={() => setIsOpen(false)}>
      Cancel
    </Button>
    <Button variant="danger" onClick={handleDelete}>
      Delete
    </Button>
  </div>
</Modal>

// Without title and close button
<Modal 
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  showCloseButton={false}
>
  <p>Custom content</p>
</Modal>
```

---

### Tooltip

Hover tooltip with multiple positions.

**Positions:** `top` | `bottom` | `left` | `right`

```jsx
<Tooltip content="This is a helpful hint" position="top">
  <button>Hover me</button>
</Tooltip>

// With custom delay
<Tooltip content="Delayed tooltip" position="right" delay={500}>
  <span>Hover for 500ms</span>
</Tooltip>
```

---

### Spinner

Loading indicator.

**Sizes:** `sm` | `md` | `lg` | `xl`  
**Colors:** `primary` | `secondary` | `success` | `danger` | `warning` | `white`

```jsx
// Basic
<Spinner />

// Large primary spinner
<Spinner size="lg" color="primary" />

// White spinner (for dark backgrounds)
<Spinner size="md" color="white" />
```

---

### Alert

Notification and message box.

**Variants:** `success` | `danger` | `warning` | `info`

```jsx
// Success message
<Alert variant="success">
  Operation completed successfully!
</Alert>

// Error with close button
<Alert variant="danger" onClose={() => setShowAlert(false)}>
  An error occurred. Please try again.
</Alert>

// Custom icon
<Alert variant="info" icon={<InfoIcon />}>
  This is important information.
</Alert>
```

---

### ThemeToggle

Dark/Light mode switcher.

```jsx
<ThemeToggle />
```

---

## 🎨 Design System

### Colors

The library uses a comprehensive color palette:

- **Primary** (Blue): Brand color, main actions
- **Accent** (Purple): Secondary actions, highlights
- **Success** (Green): Positive actions, profit
- **Danger** (Red): Destructive actions, loss
- **Warning** (Amber): Warnings, caution
- **Info** (Cyan): Information, neutral
- **Dark** (Grays): Theme-based backgrounds

Each color has 11 shades (50-950) for granular control.

### Typography

- **Sans:** Inter (UI text)
- **Mono:** JetBrains Mono (code, numbers)

### Spacing

8px base grid: `0.5`, `1`, `1.5`, `2`, `2.5`, `3`, `4`, `6`, `8`, `12`, `16`, `20`, `24`

---

## 🌗 Theme Support

All components automatically adapt to dark/light themes:

```jsx
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

function App() {
  return (
    <ThemeProvider>
      <YourApp />
    </ThemeProvider>
  );
}

function Component() {
  const { theme, toggleTheme, isDark } = useTheme();
  
  return (
    <button onClick={toggleTheme}>
      Current: {theme}
    </button>
  );
}
```

---

## ♿ Accessibility

All components include:
- ARIA attributes
- Keyboard navigation
- Focus management
- Screen reader support

---

## 📝 Best Practices

1. **Consistent Variants:** Use semantic variants (`success`, `danger`) over colors
2. **Size Hierarchy:** Stick to defined sizes for consistency
3. **Theme Awareness:** Components automatically adapt - don't hardcode colors
4. **Composition:** Use Card sub-components for better structure
5. **Loading States:** Always show feedback for async actions

---

## 🚀 Performance

- **Tree-shakeable:** Import only what you need
- **Lightweight:** No external dependencies (except lucide-react for icons)
- **Optimized:** Minimal re-renders with proper prop handling

---

## 📦 Component Sizes

| Component | Lines | Features |
|-----------|-------|----------|
| Button | 93 | 7 variants, loading, icons |
| Card | 69 | 4 variants, composition |
| Input | 97 | Validation, icons, errors |
| Badge | 54 | 7 variants, dot indicator |
| Select | 119 | Dropdown, validation |
| Modal | 110 | 5 sizes, backdrop blur |
| Tooltip | 95 | 4 positions, delay |
| Spinner | 42 | 6 colors, 4 sizes |
| Alert | 68 | 4 types, close button |
| ThemeToggle | 44 | Dark/Light switch |

**Total:** ~791 lines of reusable UI code
