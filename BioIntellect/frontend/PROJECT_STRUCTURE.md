# 📂 Project Structure Overview

Complete visual map of BioIntellect Frontend project.

---

## 🎯 Directory Tree

```
BioIntellect/frontend/
│
├── 📄 Configuration Files
│   ├── package.json                    # Dependencies & scripts
│   ├── vite.config.js                  # Vite build config
│   ├── tsconfig.json                   # TypeScript config
│   ├── tsconfig.node.json              # TS config for Node
│   ├── .gitignore                      # Git ignore rules
│   └── index.html                      # HTML entry point
│
├── 📚 Documentation Files
│   ├── README.md                       # Main documentation
│   ├── QUICK_START.md                  # Getting started guide
│   ├── COMPONENTS.md                   # Component reference
│   ├── SUPABASE_INTEGRATION.md         # Supabase setup guide
│   └── PROJECT_COMPLETION.md           # Completion summary
│
├── 📁 src/
│   │
│   ├── 🎨 components/                  # Reusable UI Components
│   │   ├── TopBar.jsx                  # Navigation bar
│   │   ├── TopBar.module.css           # TopBar styles
│   │   ├── AnimatedButton.jsx          # Button component
│   │   ├── AnimatedButton.module.css   # Button styles
│   │   ├── InputField.jsx              # Form input component
│   │   └── InputField.module.css       # Input styles
│   │
│   ├── 📄 pages/                       # Page Components
│   │   ├── SelectRole.jsx              # Role selection page
│   │   ├── SelectRole.module.css       # SelectRole styles
│   │   ├── Login.jsx                   # Login page
│   │   ├── Login.module.css            # Login styles
│   │   ├── SignUp.jsx                  # Registration page
│   │   ├── SignUp.module.css           # SignUp styles
│   │   ├── ResetPassword.jsx           # Password recovery page
│   │   └── ResetPassword.module.css    # ResetPassword styles
│   │
│   ├── 🧠 context/                     # State Management
│   │   └── AuthContext.jsx             # Global auth state
│   │
│   ├── 🎨 styles/                      # Global Styles
│   │   └── theme.css                   # Design system
│   │
│   ├── App.jsx                         # Main app component
│   └── main.jsx                        # React DOM entry
│
└── 📦 public/                          # Static assets (empty)

```

---

## 📊 File Count & Organization

| Category | Count | Total |
|----------|-------|-------|
| Configuration | 5 | 5 |
| Documentation | 5 | 5 |
| Components | 6 | 6 |
| Pages | 8 | 8 |
| Context | 1 | 1 |
| Styles | 1 | 1 |
| Entry Points | 2 | 2 |
| **TOTAL** | - | **28** |

---

## 🔍 Detailed Breakdown

### Configuration Files (5)

```
package.json
├── Dependencies
│   ├── react@18.3.1
│   ├── react-dom@18.3.1
│   └── framer-motion@11.0.3
│
└── Dev Dependencies
    ├── @vitejs/plugin-react@4.2.1
    └── vite@5.0.8

vite.config.js
├── React plugin
└── Dev server config (port 5173)

tsconfig.json
├── Compilation options
└── Module resolution

tsconfig.node.json
└── Config for Node environment

.gitignore
├── node_modules
├── dist
├── .env.local
└── Editor files
```

### Documentation (5)

| File | Purpose | Size |
|------|---------|------|
| README.md | Complete guide | ~400 lines |
| QUICK_START.md | Getting started | ~250 lines |
| COMPONENTS.md | Component docs | ~350 lines |
| SUPABASE_INTEGRATION.md | Supabase setup | ~400 lines |
| PROJECT_COMPLETION.md | Completion summary | ~300 lines |

---

### src/components/ (6)

#### TopBar Component
```
TopBar/
├── TopBar.jsx              # Functional component
│   ├── Props
│   │   └── userRole: string
│   │
│   ├── Features
│   │   ├── Logo/branding
│   │   ├── User role display
│   │   └── Fixed positioning
│   │
│   └── Exports
│       └── TopBar component
│
└── TopBar.module.css       # Styles
    ├── .topbar (fixed nav)
    ├── .brand (logo)
    └── .roleLabel (role badge)
```

#### AnimatedButton Component
```
AnimatedButton/
├── AnimatedButton.jsx
│   ├── Props
│   │   ├── children
│   │   ├── variant (primary|secondary|outline)
│   │   ├── size (small|medium|large)
│   │   ├── isLoading
│   │   ├── disabled
│   │   ├── onClick
│   │   └── fullWidth
│   │
│   ├── Features
│   │   ├── Framer Motion animations
│   │   ├── Loading spinner
│   │   ├── Multiple variants
│   │   └── Multiple sizes
│   │
│   └── Exports
│       └── AnimatedButton component
│
└── AnimatedButton.module.css
    ├── .primary, .secondary, .outline
    ├── .small, .medium, .large
    ├── .fullWidth
    ├── Loading spinner animation
    └── States (hover, active, disabled)
```

#### InputField Component
```
InputField/
├── InputField.jsx
│   ├── Props
│   │   ├── id
│   │   ├── label
│   │   ├── type (text|email|password|...)
│   │   ├── value
│   │   ├── onChange
│   │   ├── error
│   │   ├── success
│   │   ├── icon
│   │   ├── helperText
│   │   ├── required
│   │   └── disabled
│   │
│   ├── Features
│   │   ├── Multiple input types
│   │   ├── Validation states
│   │   ├── Icon support
│   │   ├── Helper text
│   │   ├── Error messages
│   │   └── Focus states
│   │
│   └── Exports
│       └── InputField component
│
└── InputField.module.css
    ├── .container (wrapper)
    ├── .input (field)
    ├── .label (label)
    ├── .icon (icon styling)
    ├── States (.error, .success, .focused)
    └── RTL support
```

---

### src/pages/ (8 - 4 Pages × 2 Files Each)

#### Page 1: SelectRole
```
SelectRole/
├── SelectRole.jsx
│   ├── State
│   │   └── selectedRole (local)
│   │
│   ├── Context
│   │   ├── selectRole()
│   │   └── useAuth()
│   │
│   ├── Features
│   │   ├── Two role cards
│   │   ├── Animations
│   │   ├── Role selection logic
│   │   └── Transition to Login
│   │
│   ├── Components Used
│   │   ├── TopBar
│   │   └── Motion elements
│   │
│   └── Navigation
│       └── onRoleSelected() → Login
│
└── SelectRole.module.css
    ├── Page layout
    ├── Role cards styling
    ├── Hover states
    ├── Animations
    └── Responsive design
```

#### Page 2: Login
```
Login/
├── Login.jsx
│   ├── State
│   │   └── formData { email, password }
│   │
│   ├── Context
│   │   ├── mockLogin()
│   │   ├── useAuth()
│   │   ├── isLoading
│   │   ├── error
│   │   └── userRole
│   │
│   ├── Features
│   │   ├── Email & password fields
│   │   ├── Form validation
│   │   ├── Error display
│   │   ├── Loading state
│   │   ├── Forgot password link
│   │   └── Sign up link
│   │
│   ├── Components Used
│   │   ├── TopBar
│   │   ├── InputField
│   │   └── AnimatedButton
│   │
│   └── Navigation
│       ├── onLoginSuccess() → Dashboard (future)
│       ├── onSignUpClick() → SignUp
│       └── onForgotPasswordClick() → ResetPassword
│
└── Login.module.css
    ├── Page layout
    ├── Card styling
    ├── Form layout
    ├── Error alert
    └── Responsive design
```

#### Page 3: SignUp
```
SignUp/
├── SignUp.jsx
│   ├── State
│   │   └── formData {
│   │       full_name,
│   │       email,
│   │       password,
│   │       password_confirm
│   │     }
│   │
│   ├── Context
│   │   ├── mockSignUp()
│   │   ├── useAuth()
│   │   ├── isLoading
│   │   ├── error
│   │   └── userRole
│   │
│   ├── Features
│   │   ├── Full name field
│   │   ├── Email field
│   │   ├── Password field
│   │   ├── Password confirmation
│   │   ├── Form validation
│   │   ├── Error display
│   │   ├── Terms agreement
│   │   └── Schema-aligned fields
│   │
│   ├── Components Used
│   │   ├── TopBar
│   │   ├── InputField
│   │   └── AnimatedButton
│   │
│   └── Navigation
│       ├── onSignUpSuccess() → Login
│       └── onLoginClick() → Login
│
└── SignUp.module.css
    ├── Page layout
    ├── Card styling
    ├── Form layout
    ├── Terms section
    └── Responsive design
```

#### Page 4: ResetPassword
```
ResetPassword/
├── ResetPassword.jsx
│   ├── State
│   │   ├── email
│   │   └── resetSent (boolean)
│   │
│   ├── Context
│   │   ├── mockResetPassword()
│   │   ├── useAuth()
│   │   ├── isLoading
│   │   ├── error
│   │   └── userRole
│   │
│   ├── Features
│   │   ├── Email input
│   │   ├── Form validation
│   │   ├── Error display
│   │   ├── Loading state
│   │   ├── Success screen
│   │   ├── Steps display
│   │   └── Send again link
│   │
│   ├── Components Used
│   │   ├── TopBar
│   │   ├── InputField
│   │   └── AnimatedButton
│   │
│   ├── States
│   │   ├── Form state (email input)
│   │   └── Success state (confirmation)
│   │
│   └── Navigation
│       ├── onResetSuccess() → Login
│       └── onBackToLogin() → Login
│
└── ResetPassword.module.css
    ├── Page layout
    ├── Card styling
    ├── Success state styles
    ├── Steps display
    └── Responsive design
```

---

### src/context/

#### AuthContext.jsx

```
AuthContext/
├── createContext()
│
├── AuthProvider Component
│   ├── State
│   │   ├── userRole
│   │   ├── isAuthenticated
│   │   ├── currentUser
│   │   ├── isLoading
│   │   └── error
│   │
│   ├── Actions
│   │   ├── selectRole(role)
│   │   ├── mockLogin(email, password)
│   │   ├── mockSignUp(full_name, email, password)
│   │   ├── mockResetPassword(email)
│   │   ├── logout()
│   │   └── clearError()
│   │
│   ├── LocalStorage
│   │   └── Persist userRole
│   │
│   └── Provides
│       └── value object with all state & actions
│
└── useAuth() Custom Hook
    └── Returns AuthContext value
```

---

### src/styles/

#### theme.css

```
Design System/
├── CSS Variables
│   ├── Colors (15+ tokens)
│   ├── Spacing (8 tokens)
│   ├── Typography (12 tokens)
│   ├── Shadows (4 tokens)
│   ├── Border Radius (5 tokens)
│   └── Transitions (3 tokens)
│
├── Global Styles
│   ├── Reset
│   ├── Body styles
│   ├── Typography
│   ├── Form elements
│   └── Scrollbar
│
├── Utility Classes
│   ├── Container
│   ├── Text align
│   ├── Margin helpers
│   └── Screen reader only
│
├── Animations
│   ├── fadeIn
│   ├── slideInUp
│   └── slideInDown
│
└── Media Queries
    ├── Tablet (768px)
    └── Mobile (480px)
```

---

### src/ Root Files

#### App.jsx
```
Main Application Component
├── State
│   └── currentPage (page navigation)
│
├── Handlers
│   ├── handleRoleSelected()
│   ├── handleLoginSuccess()
│   ├── handleSignUpSuccess()
│   ├── handleResetPassword()
│   ├── handleResetSuccess()
│   └── handleBackToLogin()
│
├── Routing Logic
│   ├── SelectRole page
│   ├── Login page
│   ├── SignUp page
│   └── ResetPassword page
│
└── Provider
    └── AuthProvider wrapper
```

#### main.jsx
```
React DOM Entry Point
├── ReactDOM.createRoot()
├── React.StrictMode
└── App component
```

---

## 🔄 Data Flow

```
User Opens App
    ↓
main.jsx
    ↓
App.jsx (with AuthProvider)
    ↓
AuthContext (Global State)
    ├── userRole
    ├── currentUser
    ├── isAuthenticated
    ├── isLoading
    └── error
    ↓
Page Components (pages/)
    ├── SelectRole.jsx
    ├── Login.jsx
    ├── SignUp.jsx
    └── ResetPassword.jsx
    ↓
Reusable Components (components/)
    ├── TopBar.jsx
    ├── AnimatedButton.jsx
    └── InputField.jsx
    ↓
Design System (theme.css)
    ├── Colors
    ├── Typography
    ├── Spacing
    └── Animations
```

---

## 📊 Dependencies Map

```
package.json
├── react@18.3.1
│   └── Used in: All components & pages
│
├── react-dom@18.3.1
│   └── Used in: main.jsx
│
└── framer-motion@11.0.3
    └── Used in: AnimatedButton, Page animations
```

---

## 🎯 Component Hierarchy

```
<App>
  <AuthProvider>
    {currentPage === 'selectRole' && <SelectRole>}
    {currentPage === 'login' && <Login>
      <TopBar />
      <InputField />
      <InputField />
      <AnimatedButton />
    </Login>}
    {currentPage === 'signUp' && <SignUp>
      <TopBar />
      <InputField />
      <InputField />
      <InputField />
      <InputField />
      <AnimatedButton />
    </SignUp>}
    {currentPage === 'resetPassword' && <ResetPassword>
      <TopBar />
      <InputField />
      <AnimatedButton />
    </ResetPassword>}
  </AuthProvider>
</App>
```

---

## 🗂️ Import Structure

```
Components
  ↓ imports from
Pages
  ↓ imports from
Context
  ↓ imports from
Styles

No circular imports
No interdependent components
Clean separation of concerns
```

---

## 📱 Mobile-First Design

Each file includes media queries:
- 768px breakpoint (tablet)
- 480px breakpoint (mobile)
- Responsive typography
- Flexible spacing
- Touch-friendly buttons

---

## 🔐 Security Structure

```
No sensitive data in:
├── Comments
├── State
├── Components
└── Styling

All validation:
├── Client-side (UX)
├── Server-side (future - Supabase)
└── Database (future - RLS)
```

---

## 📈 Scalability

Ready for:
```
Current (4 pages)
    ↓
Next (Add dashboard pages)
    ↓
Later (Add admin pages)
    ↓
Future (Add mobile app)
```

**No refactoring needed** - structure supports growth.

---

## 🎓 Learning Path

**Beginner**: Read `README.md` → Run `npm run dev`  
**Intermediate**: Review component code → Check styling  
**Advanced**: Study Context → Implement Supabase  

---

## ✅ Checklist for Understanding

- [ ] Know location of each component
- [ ] Understand file naming convention
- [ ] Know import structure
- [ ] Understand data flow
- [ ] Know design system location
- [ ] Understand page routing
- [ ] Know context structure

---

**Project is well-organized, scalable, and easy to maintain!**
