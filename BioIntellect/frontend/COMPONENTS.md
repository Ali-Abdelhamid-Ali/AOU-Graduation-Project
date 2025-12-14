# 📦 Components Documentation

Complete reference for all reusable components in BioIntellect.

---

## 📋 Table of Contents

1. [TopBar](#topbar)
2. [AnimatedButton](#animatedbutton)
3. [InputField](#inputfield)

---

## TopBar

**Location**: `src/components/TopBar.jsx`

Fixed navigation bar at the top of the application.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `userRole` | string | null | User role ('doctor' or 'patient') |

### Features

- ✅ Fixed positioning
- ✅ Logo/branding
- ✅ User role display
- ✅ Professional healthcare design
- ✅ Responsive layout

### Usage

```jsx
import { TopBar } from '../components/TopBar'

export function MyPage() {
  return (
    <>
      <TopBar userRole="doctor" />
      {/* Rest of page */}
    </>
  )
}
```

### Styling

- **Height**: 64px (desktop), 56px (mobile)
- **Background**: White
- **Shadow**: Subtle shadow
- **Z-index**: 1200 (stays on top)

### Customization

Edit `TopBar.module.css`:
- Change colors in `.topbar`
- Adjust height in `.topbar`
- Modify logo styling in `.logo`

---

## AnimatedButton

**Location**: `src/components/AnimatedButton.jsx`

Reusable button component with smooth Framer Motion animations.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | ReactNode | required | Button text/content |
| `onClick` | function | undefined | Click handler |
| `variant` | string | 'primary' | Style variant |
| `size` | string | 'medium' | Button size |
| `disabled` | boolean | false | Disable button |
| `isLoading` | boolean | false | Show loading state |
| `type` | string | 'button' | HTML button type |
| `fullWidth` | boolean | false | Stretch to container width |
| `className` | string | '' | Additional CSS classes |

### Variants

#### Primary
```jsx
<AnimatedButton variant="primary">
  Submit
</AnimatedButton>
```
- Background: Soft blue
- Text: White
- Use for: Main actions

#### Secondary
```jsx
<AnimatedButton variant="secondary">
  Continue
</AnimatedButton>
```
- Background: Teal
- Text: White
- Use for: Alternative actions

#### Outline
```jsx
<AnimatedButton variant="outline">
  Cancel
</AnimatedButton>
```
- Background: Transparent
- Border: Blue outline
- Use for: Secondary/cancel actions

### Sizes

#### Small
```jsx
<AnimatedButton size="small">Confirm</AnimatedButton>
```
- Padding: 8px 16px
- Font: 14px

#### Medium (Default)
```jsx
<AnimatedButton size="medium">Submit</AnimatedButton>
```
- Padding: 12px 24px
- Font: 16px

#### Large
```jsx
<AnimatedButton size="large">Next Step</AnimatedButton>
```
- Padding: 16px 32px
- Font: 18px
- Min height: 48px

### States

#### Normal State
```jsx
<AnimatedButton onClick={handleClick}>
  Click Me
</AnimatedButton>
```

#### Disabled State
```jsx
<AnimatedButton disabled>
  Disabled
</AnimatedButton>
```
- Opacity: 60%
- Cursor: not-allowed

#### Loading State
```jsx
<AnimatedButton isLoading={isLoading}>
  Submit
</AnimatedButton>
```
- Shows spinner
- Disabled automatically
- Text: "Processing..."

### Animations

- **Hover**: Scale to 102%
- **Click**: Scale to 98%
- **Transition**: Spring (stiffness: 400, damping: 17)

### Usage Examples

```jsx
import { AnimatedButton } from '../components/AnimatedButton'

// Simple button
<AnimatedButton onClick={() => alert('Clicked!')}>
  Click Me
</AnimatedButton>

// Full width form button
<AnimatedButton
  type="submit"
  variant="primary"
  size="large"
  fullWidth
>
  Login
</AnimatedButton>

// Loading button
<AnimatedButton
  onClick={handleSubmit}
  isLoading={isSubmitting}
  variant="secondary"
>
  Save Changes
</AnimatedButton>

// Outline button
<AnimatedButton
  variant="outline"
  onClick={handleCancel}
>
  Cancel
</AnimatedButton>
```

### Accessibility

- ✅ Focus indicator visible
- ✅ Keyboard navigable
- ✅ ARIA states for disabled
- ✅ Loading state announced

---

## InputField

**Location**: `src/components/InputField.jsx`

Flexible form input component with validation, icons, and helper text.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `id` | string | required | Unique input ID |
| `label` | string | undefined | Field label |
| `type` | string | 'text' | Input type |
| `placeholder` | string | undefined | Placeholder text |
| `value` | string | required | Current value |
| `onChange` | function | required | Change handler |
| `error` | string | undefined | Error message |
| `success` | boolean | false | Show success state |
| `disabled` | boolean | false | Disable input |
| `required` | boolean | false | Mark as required |
| `icon` | string | null | Icon emoji |
| `helperText` | string | undefined | Helper text below |

### Types

All standard HTML input types:
- `text`
- `email`
- `password`
- `number`
- `tel`
- `url`
- etc.

### Usage Examples

```jsx
import { InputField } from '../components/InputField'
import { useState } from 'react'

function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})

  return (
    <>
      {/* Email input */}
      <InputField
        id="email"
        label="Email Address"
        type="email"
        placeholder="example@hospital.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={errors.email}
        required
        icon="✉️"
      />

      {/* Password input */}
      <InputField
        id="password"
        label="Password"
        type="password"
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={errors.password}
        required
        icon="🔐"
      />

      {/* With helper text */}
      <InputField
        id="confirm_password"
        label="Confirm Password"
        type="password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        helperText="Must match password above"
        icon="🔐"
      />
    </>
  )
}
```

### Validation Example

```jsx
const [email, setEmail] = useState('')
const [error, setError] = useState('')

const handleEmailChange = (value) => {
  setEmail(value)
  
  // Clear error on change
  if (error) setError('')
  
  // Validate
  if (value && !value.includes('@')) {
    setError('Invalid email format')
  }
}

<InputField
  id="email"
  label="Email"
  type="email"
  value={email}
  onChange={(e) => handleEmailChange(e.target.value)}
  error={error}
  required
/>
```

### States

#### Normal State
```jsx
<InputField
  id="name"
  label="Full Name"
  placeholder="Enter your name"
  value={name}
  onChange={(e) => setName(e.target.value)}
/>
```

#### With Error
```jsx
<InputField
  id="email"
  label="Email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  error="Invalid email format"
/>
```
- Red border
- Red error message
- Error icon: ⚠️

#### With Success
```jsx
<InputField
  id="password"
  label="Password"
  type="password"
  value={password}
  onChange={(e) => setPassword(e.target.value)}
  success={true}
/>
```
- Green border
- Indicates valid input

#### Disabled State
```jsx
<InputField
  id="readonly"
  label="User ID"
  value="user-123"
  disabled={true}
  onChange={() => {}}
/>
```

#### With Icon
```jsx
<InputField
  id="email"
  label="Email"
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  icon="✉️"
/>
```

Icons align right (RTL support).

#### With Helper Text
```jsx
<InputField
  id="password"
  label="Password"
  type="password"
  value={password}
  onChange={(e) => setPassword(e.target.value)}
  helperText="Minimum 6 characters"
/>
```

### Styling

- **Border**: 2px solid gray
- **Border Radius**: 8px
- **Padding**: 12px 16px
- **Font Size**: 16px (mobile)
- **Focus**: Blue border + light blue shadow

### Accessibility

- ✅ Associated label
- ✅ Unique ID
- ✅ Error messages
- ✅ Helper text
- ✅ Focus indicator
- ✅ RTL support
- ✅ Screen reader friendly

### Theme Colors

- **Border**: `var(--color-gray-300)`
- **Focus**: `var(--color-primary)`
- **Error**: `var(--color-error)`
- **Success**: `var(--color-success)`
- **Background**: White

---

## Creating New Components

### Template

```jsx
/**
 * MyComponent
 * 
 * Brief description
 * Features:
 * - Feature 1
 * - Feature 2
 */

import styles from './MyComponent.module.css'

export const MyComponent = ({
  // Props
  prop1,
  prop2 = 'default',
}) => {
  return (
    <div className={styles.container}>
      {/* Component JSX */}
    </div>
  )
}
```

### CSS Module Template

```css
.container {
  /* Styles */
}

@media (max-width: 768px) {
  .container {
    /* Mobile styles */
  }
}
```

---

## Best Practices

✅ **Do**
- Use descriptive prop names
- Add PropTypes or TypeScript
- Include accessibility features
- Use CSS modules
- Document with comments
- Test different states
- Support RTL layout

❌ **Don't**
- Hardcode colors (use CSS variables)
- Skip accessibility
- Use inline styles
- Create components too large
- Forget responsive design
- Mix styling approaches

---

## Extending Components

### Adding Props

```jsx
export const InputField = ({
  // ... existing props
  maxLength,           // New prop
  inputMode = 'text',  // New prop with default
}) => {
  return (
    <input
      maxLength={maxLength}
      inputMode={inputMode}
      {/* ... rest */}
    />
  )
}
```

### Adding Variants

```jsx
export const AnimatedButton = ({
  // ... existing props
  variant = 'primary',
}) => {
  return (
    <button
      className={`${styles.button} ${styles[variant]}`}
      {/* ... rest */}
    >
      {children}
    </button>
  )
}

// In CSS
.primary { /* ... */ }
.secondary { /* ... */ }
.tertiary { /* ... */ }  // New variant
```

---

## Performance Tips

- Use `React.memo()` for expensive components
- Avoid unnecessary re-renders
- Use CSS for animations (faster than JS)
- Lazy load components if needed
- Keep props minimal

---

## Testing Components

```jsx
import { render, screen } from '@testing-library/react'
import { AnimatedButton } from './AnimatedButton'

test('renders button with text', () => {
  render(<AnimatedButton>Click Me</AnimatedButton>)
  expect(screen.getByText('Click Me')).toBeInTheDocument()
})

test('calls onClick handler', () => {
  const handleClick = jest.fn()
  render(<AnimatedButton onClick={handleClick}>Click</AnimatedButton>)
  screen.getByText('Click').click()
  expect(handleClick).toHaveBeenCalled()
})
```

---

**Happy building! 🚀**
