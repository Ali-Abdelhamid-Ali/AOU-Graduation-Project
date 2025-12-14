# BioIntellect Frontend - Enhanced Version 2.0

**Advanced Medical Intelligence Platform** - React 18 + Supabase + Anime.js + Framer Motion

## ✨ What's New in v2.0

### 🎨 Advanced Animations
- ✅ **Anime.js** - Professional animation library
- ✅ **Framer Motion** - Smooth motion effects
- ✅ Custom animation hooks (`useAnimations`)
- ✅ Stagger animations for lists
- ✅ Scroll-triggered animations

### 🔐 Supabase Integration
- ✅ Real authentication with Supabase
- ✅ Database-driven user management
- ✅ API service layer (`api.js`)
- ✅ Secure password reset flow
- ✅ Email verification support

### 🏗️ Better Architecture
- ✅ Config folder for Supabase setup
- ✅ Services layer for API calls
- ✅ Utils folder for helpers
- ✅ Hooks folder for reusable logic
- ✅ Improved error handling

### 🎯 Premium UI/UX
- ✅ Production-ready design
- ✅ Perfect spacing and typography
- ✅ Gradient backgrounds
- ✅ Shadow effects
- ✅ RTL-ready (Arabic support)

## 📦 Installation

```bash
# 1. Install dependencies
npm install

# 2. Create .env.local from template
cp .env.local.example .env.local

# 3. Add your Supabase credentials to .env.local
# Get from: https://supabase.com/dashboard

# 4. Start development server
npm run dev
```

## 🚀 Getting Started

### 1. Setup Supabase

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Go to Settings → API
4. Copy your **URL** and **anon key**
5. Paste into `.env.local`:

```env
VITE_SUPABASE_URL=your_url_here
VITE_SUPABASE_ANON_KEY=your_key_here
```

### 2. Create Database Tables

In Supabase SQL Editor, run:

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  user_role TEXT DEFAULT 'patient',
  is_verified BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS (Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
```

### 3. Run Development Server

```bash
npm run dev
```

Visit `http://localhost:5173`

## 📂 Project Structure

```
frontend/
├── src/
│   ├── config/           # Configuration files
│   │   └── supabase.js  # Supabase client
│   ├── context/         # React Context
│   │   └── AuthContext.jsx
│   ├── components/      # Reusable components
│   │   ├── AnimatedButton.jsx
│   │   ├── InputField.jsx
│   │   └── TopBar.jsx
│   ├── pages/          # Page components
│   │   ├── Login.jsx
│   │   ├── SignUp.jsx
│   │   ├── SelectRole.jsx
│   │   └── ResetPassword.jsx
│   ├── services/       # API services
│   │   └── api.js     # Supabase API calls
│   ├── hooks/         # Custom React hooks
│   │   └── useAnimations.js
│   ├── utils/         # Utility functions
│   │   └── animations.js
│   ├── styles/        # CSS stylesheets
│   │   └── theme.css
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── .env.local.example  # Environment template
├── package.json
└── vite.config.js
```

## 🎬 Animation Features

### Built-in Animations

1. **Fade In/Out** - Element appears smoothly
2. **Slide In** - Element slides from edge
3. **Scale Pop** - Bouncy scale effect
4. **Bounce** - Jump animation
5. **Shake** - Error feedback
6. **Glow** - Success indication
7. **Stagger** - List item animations
8. **Pulse** - Attention animation

### Using Animations

```jsx
import { useSlideInAnimation, useStaggerAnimation } from '../hooks/useAnimations'

// Slide element up on mount
const ref = useSlideInAnimation(true, 'up')
<div ref={ref}>Content</div>

// Stagger list items
const listRef = useStaggerAnimation(items, { 
  duration: 500, 
  staggerDelay: 100 
})
<div ref={listRef}>
  {items.map(item => <div key={item.id}>{item}</div>)}
</div>
```

## 🔑 Key Dependencies

| Package | Purpose |
|---------|---------|
| `react` | UI framework |
| `react-dom` | React for web |
| `framer-motion` | React animations |
| `animejs` | Advanced animations |
| `@supabase/supabase-js` | Backend & auth |

## 🔐 Authentication Flow

```
1. SelectRole Page
   ↓
2. Login / SignUp
   ↓
3. Supabase Auth (Email/Password)
   ↓
4. User data stored in database
   ↓
5. Dashboard (coming soon)
```

## 🌐 Available Routes

| Page | Path |
|------|------|
| Role Selection | `/` |
| Login | `/login` |
| Sign Up | `/signup` |
| Reset Password | `/reset-password` |
| Dashboard | `/dashboard` (coming) |

## 🎨 Customization

### Change Colors

Edit `src/styles/theme.css`:

```css
:root {
  --color-primary: #0052cc;        /* Change primary color */
  --color-secondary: #0d7377;      /* Change secondary color */
  --color-success: #1b7e3f;        /* Change success color */
  /* ... etc */
}
```

### Change Typography

```css
:root {
  --font-family: 'Your Font', sans-serif;
  --font-size-base: 16px;
  --font-weight-semibold: 600;
  /* ... etc */
}
```

## 🧪 Testing

Test authentication flow:

1. Navigate to `/` → Select role
2. Go to Sign Up → Create account
3. Check Supabase for new user
4. Login with credentials
5. Check console for errors

## 📱 Responsive Design

Breakpoints:
- **Desktop**: 1280px+
- **Tablet**: 768px - 1279px
- **Mobile**: < 768px

All components are fully responsive!

## 🚢 Deployment

### Build for Production

```bash
npm run build
```

### Deploy to Vercel

```bash
vercel deploy
```

### Deploy to Netlify

```bash
npm run build
# Drag & drop dist/ folder to Netlify
```

## 🐛 Troubleshooting

### Supabase Connection Error

```
"Missing Supabase environment variables"
```

**Solution:**
- Check `.env.local` exists
- Verify `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are correct
- Restart dev server after editing `.env.local`

### Animation Not Working

```jsx
// Make sure to import the hook
import { useSlideInAnimation } from '../hooks/useAnimations'
```

### CORS Error

Make sure Supabase URL is correct:
```
https://[PROJECT-REF].supabase.co
```

Not:
```
https://[PROJECT-REF].supabase.co/ (with trailing slash)
```

## 📖 Documentation

- [Supabase Docs](https://supabase.com/docs)
- [Framer Motion Docs](https://www.framer.com/motion)
- [Anime.js Docs](https://animejs.com/documentation)
- [React Docs](https://react.dev)

## 📝 License

MIT

## 🤝 Support

For issues and questions:
1. Check documentation files
2. Review error messages
3. Check browser console
4. Check Supabase dashboard

---

**Made with ❤️ for medical intelligence**
