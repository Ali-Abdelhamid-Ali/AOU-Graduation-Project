# 🏥 BioIntellect - Medical Intelligence Platform

Frontend application for the BioIntellect medical system, built with React, Functional Components, and Hooks.

---

## 📋 Project Overview

**BioIntellect** is a modern, clean, and healthcare-grade web application designed for both doctors and patients. The application features:

✅ **Modern Medical UI** - Healthcare SaaS inspired design  
✅ **Eye-friendly Design** - Reduced visual stress (Human Factors Engineering)  
✅ **RTL Support** - Arabic language ready  
✅ **100% Ready for Supabase** - No backend logic, schema-aligned  
✅ **Functional Components Only** - React Hooks pattern  
✅ **Context API State Management** - No Redux  
✅ **Accessibility** - WCAG 2.1 compliance  
✅ **Responsive Design** - Mobile-first approach  

---

## 🎨 Design System

### Color Palette

**Medical-Grade Colors (Eye-Friendly)**

| Element | Color | Use Case |
|---------|-------|----------|
| Primary | `#1976d2` (Soft Blue) | Main actions, buttons |
| Secondary | `#00897b` (Teal) | Alternative actions |
| Success | `#2e7d32` (Green) | Positive feedback |
| Warning | `#f57c00` (Orange) | Warnings |
| Error | `#c62828` (Red) | Error messages |
| Background | `#fafafa` (Off-white) | Page background |

### Typography

- **Font Family**: System fonts (Inter, Segoe UI, etc.)
- **Contrast Ratio**: 4.5:1 (WCAG AA standard)
- **Font Sizes**: 12px - 30px (responsive)

### Animations

- **Framer Motion** for smooth transitions
- Minimal, healthcare-appropriate animations
- Page transitions: Fade/Slide
- Button interactions: Hover/Tap effects

---

## 🗂️ Project Structure

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── TopBar.jsx              # Fixed navigation bar
│   │   ├── TopBar.module.css
│   │   ├── AnimatedButton.jsx      # Reusable button component
│   │   ├── AnimatedButton.module.css
│   │   ├── InputField.jsx          # Form input with validation
│   │   └── InputField.module.css
│   │
│   ├── pages/
│   │   ├── SelectRole.jsx          # Step 0: Role selection
│   │   ├── SelectRole.module.css
│   │   ├── Login.jsx               # Step 1: Login
│   │   ├── Login.module.css
│   │   ├── SignUp.jsx              # Step 2: Registration
│   │   ├── SignUp.module.css
│   │   ├── ResetPassword.jsx       # Step 3: Password recovery
│   │   └── ResetPassword.module.css
│   │
│   ├── context/
│   │   └── AuthContext.jsx         # Global auth state management
│   │
│   ├── styles/
│   │   └── theme.css               # Design system & global styles
│   │
│   ├── App.jsx                     # Main app component (router logic)
│   ├── main.jsx                    # React DOM entry point
│   └── App.css
│
├── index.html                      # HTML entry point
├── package.json                    # Dependencies
├── vite.config.js                  # Vite configuration
├── tsconfig.json                   # TypeScript config
└── README.md                       # This file
```

---

## 🧠 User Flow

### Step 0: Role Selection (`SelectRole`)

User chooses their role:
- **👨‍⚕️ Doctor** - Healthcare provider
- **👤 Patient** - Medical patient

**State Storage**: React Context + LocalStorage

### Step 1: Login (`Login`)

User logs in with:
- Email ✉️
- Password 🔐

**Features**:
- Form validation
- Error handling
- Forgot password link
- Sign up link
- Loading state

### Step 2: Sign Up (`SignUp`)

User registers with:
- Full Name (`full_name`)
- Email (`email`)
- Password
- Confirm Password

**Schema Alignment**:
- Field names match Supabase `users` table
- Ready for Auth integration

### Step 3: Reset Password (`ResetPassword`)

User recovers forgotten password:
- Enter email
- Receive reset link (mocked)
- Success confirmation screen

---

## 🗄️ Supabase Integration Ready

### Aligned Schema

The form field names are designed to match Supabase users table:

```javascript
// Current state (schema-aligned)
{
  id: 'user-xxx',                    // supabase auth user id
  email: 'doctor@hospital.com',      // users.email
  full_name: 'Dr. Ahmed',            // users.full_name
  user_role: 'doctor',               // users.user_role
  is_verified: true,                 // users.is_verified
  is_active: true,                   // users.is_active
}
```

### Integration Points

When connecting to Supabase:

1. **Replace `mockLogin()`** with `supabase.auth.signInWithPassword()`
2. **Replace `mockSignUp()`** with `supabase.auth.signUp()`
3. **Replace `mockResetPassword()`** with `supabase.auth.resetPasswordForEmail()`
4. **Query users table** for additional profile data

---

## ⚡ State Management

### AuthContext

```javascript
// Available in components via: useAuth()
{
  // State
  userRole,           // 'doctor' | 'patient'
  isAuthenticated,    // boolean
  currentUser,        // { id, email, full_name, ... }
  isLoading,          // boolean
  error,              // string | null

  // Actions
  selectRole(role),
  mockLogin(email, password),
  mockSignUp(full_name, email, password),
  mockResetPassword(email),
  logout(),
  clearError(),
}
```

### Usage in Components

```jsx
import { useAuth } from '../context/AuthContext'

function MyComponent() {
  const { userRole, currentUser, isLoading, error } = useAuth()
  
  // Use context values
}
```

---

## 🚀 Installation & Development

### Prerequisites

- Node.js 16+
- npm or yarn

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Currently, **no environment variables** are needed (using mock functions).

When integrating Supabase, create `.env.local`:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

---

## 🎨 UI Components

### TopBar
- Fixed navigation
- Logo/branding
- User role display
- Professional healthcare design

### AnimatedButton
- Variants: `primary`, `secondary`, `outline`
- Sizes: `small`, `medium`, `large`
- States: `loading`, `disabled`, `active`
- Framer Motion animations

### InputField
- Types: text, email, password, number, textarea
- Validation states: error, success
- Icons support
- Helper text
- RTL support

---

## ♿ Accessibility Features

✅ **Contrast Ratio**: 4.5:1 (WCAG AA)  
✅ **Focus Indicators**: Clear visual feedback  
✅ **Semantic HTML**: Proper form elements  
✅ **ARIA Labels**: Accessible for screen readers  
✅ **Keyboard Navigation**: Full keyboard support  
✅ **Loading States**: User awareness  
✅ **Error Messages**: Clear and helpful  

---

## 📱 Responsive Design

Optimized for:
- 📱 Mobile (320px+)
- 📱 Tablet (768px+)
- 💻 Desktop (1280px+)

---

## 🔐 Security Notes

⚠️ **This is a frontend demo**. When integrating Supabase:

1. **Never hardcode credentials**
2. **Use Row Level Security (RLS)** in Supabase
3. **Enable email verification** for new accounts
4. **Implement HTTPS only** in production
5. **Use secure password reset** tokens
6. **Validate on backend** (Supabase)

---

## 🎯 Future Enhancements

Ready for:
- ✅ Dashboard pages (Doctor / Patient)
- ✅ Patient management system
- ✅ Medical records
- ✅ Appointment scheduling
- ✅ AI-powered diagnosis support
- ✅ RBAC implementation (Admin, Doctor, Patient)
- ✅ Multi-language support

---

## 📚 Technology Stack

| Category | Technology |
|----------|-----------|
| Framework | React 18 |
| Build Tool | Vite |
| State Management | React Context + Hooks |
| Animations | Framer Motion |
| Styling | CSS Modules |
| Form Handling | React Hooks |
| Type Safety | TypeScript-ready |
| Accessibility | WCAG 2.1 |

---

## 🔗 Supabase Integration Guide

### Step 1: Create Supabase Project

```bash
# Setup at https://supabase.com
```

### Step 2: Create users table

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  user_role TEXT CHECK (user_role IN ('doctor', 'patient')),
  is_verified BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
```

### Step 3: Install Supabase client

```bash
npm install @supabase/supabase-js
```

### Step 4: Create Supabase service

```javascript
// src/services/supabaseClient.js
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)
```

### Step 5: Update AuthContext

Replace mock functions with Supabase calls in `src/context/AuthContext.jsx`:

```javascript
const mockLogin = async (email, password) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  
  if (error) {
    setError(error.message)
    return
  }
  
  setIsAuthenticated(true)
  setCurrentUser(data.user)
}
```

---

## 🤝 Contributing

This is a frontend foundation for BioIntellect. Follow these guidelines:

1. **Component Naming**: PascalCase (e.g., `MyComponent.jsx`)
2. **Hook Naming**: Starts with `use` (e.g., `useAuth()`)
3. **CSS Modules**: One per component (e.g., `MyComponent.module.css`)
4. **No Redux**: Use Context API for state
5. **Functional Components Only**: No class components
6. **Accessibility First**: WCAG 2.1 compliance

---

## 📄 License

This project is part of the AOU Graduation Project.

---

## 👨‍💼 Project Information

**Project Name**: BioIntellect  
**Type**: Medical Intelligence Platform  
**Team**: AOU Graduation Project  
**Status**: Frontend Ready for Supabase Integration  

---

## ❓ FAQ

### Q: Why no Redux?
**A**: For this project's scope, Context API + Hooks is sufficient. Redux adds unnecessary complexity for a simple authentication flow.

### Q: Is this production-ready?
**A**: The UI/UX is production-ready. Backend integration (Supabase) is needed before production deployment.

### Q: Can I customize the colors?
**A**: Yes! All colors are in `src/styles/theme.css` as CSS variables. Update `--color-*` variables.

### Q: How do I add more pages?
**A**: Create a new file in `src/pages/`, add navigation in `App.jsx`, and import it.

### Q: Is it mobile-friendly?
**A**: Yes! Built with mobile-first responsive design. Tested on 320px+ screens.

---

## 📞 Support

For questions or issues, refer to:
- [React Documentation](https://react.dev)
- [Supabase Documentation](https://supabase.com/docs)
- [Framer Motion Documentation](https://www.framer.com/motion)
- [Vite Documentation](https://vitejs.dev)

---

**Built with ❤️ for Healthcare**
