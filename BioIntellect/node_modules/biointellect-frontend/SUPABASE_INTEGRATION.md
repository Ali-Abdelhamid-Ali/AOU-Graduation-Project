# 🔗 Supabase Integration Guide

This document provides step-by-step instructions for integrating Supabase with BioIntellect Frontend.

---

## 📋 Pre-Integration Checklist

Before integrating Supabase:

- [ ] Supabase account created
- [ ] Project initialized on Supabase
- [ ] Database schema created (see below)
- [ ] API credentials obtained
- [ ] Email service configured (for password reset)

---

## 🗄️ Database Schema

Create the following tables in your Supabase project:

### 1. users Table

```sql
-- Create users table
CREATE TABLE users (
  -- Authentication
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  
  -- Profile
  full_name TEXT,
  user_role TEXT CHECK (user_role IN ('doctor', 'patient', 'admin')),
  
  -- Status
  is_verified BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT valid_full_name CHECK (char_length(full_name) >= 3)
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create index for faster queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(user_role);
```

### 2. RLS (Row Level Security) Policies

```sql
-- Policy 1: Users can read their own record
CREATE POLICY "Users can read own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- Policy 2: Users can update their own record
CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Policy 3: New users can insert their own record
CREATE POLICY "Users can create own profile"
  ON users FOR INSERT
  WITH CHECK (auth.uid() = id);
```

### 3. Doctor-Specific Table (Optional)

```sql
CREATE TABLE doctors (
  id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  specialization TEXT,
  license_number TEXT UNIQUE,
  hospital TEXT,
  verified_by_admin BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;
```

### 4. Patient-Specific Table (Optional)

```sql
CREATE TABLE patients (
  id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  date_of_birth DATE,
  gender TEXT CHECK (gender IN ('M', 'F', 'O')),
  blood_type TEXT,
  medical_history TEXT,
  emergency_contact TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
```

---

## 🛠️ Installation

### Step 1: Install Supabase Client

```bash
npm install @supabase/supabase-js
```

### Step 2: Create Environment Variables

Create `.env.local` in the project root:

```env
VITE_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

Get these values from Supabase Dashboard:
- Go to Settings → API
- Copy `Project URL` and `anon` key

### Step 3: Create Supabase Client

Create `src/services/supabaseClient.js`:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase credentials in environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

---

## 🔄 Updating AuthContext

Replace mock functions in `src/context/AuthContext.jsx`:

### Replace mockLogin()

```javascript
import { supabase } from '../services/supabaseClient'

const mockLogin = async (email, password) => {
  setIsLoading(true)
  setError(null)

  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) throw error

    // Fetch user profile from users table
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('*')
      .eq('id', data.user.id)
      .single()

    if (userError) throw userError

    setIsAuthenticated(true)
    setCurrentUser({
      id: data.user.id,
      email: data.user.email,
      full_name: userData.full_name,
      user_role: userData.user_role,
      is_verified: userData.is_verified,
      is_active: userData.is_active,
    })

    setIsLoading(false)
  } catch (err) {
    setError(err.message)
    setIsLoading(false)
  }
}
```

### Replace mockSignUp()

```javascript
const mockSignUp = async (full_name, email, password) => {
  setIsLoading(true)
  setError(null)

  try {
    // Sign up with Supabase Auth
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name,
          user_role: userRole,
        },
      },
    })

    if (error) throw error

    // Create user profile in users table
    const { error: profileError } = await supabase
      .from('users')
      .insert([
        {
          id: data.user.id,
          email,
          full_name,
          user_role: userRole,
          is_verified: false,
          is_active: true,
        },
      ])

    if (profileError) throw profileError

    setIsAuthenticated(true)
    setCurrentUser({
      id: data.user.id,
      email,
      full_name,
      user_role: userRole,
      is_verified: false,
      is_active: true,
    })

    setIsLoading(false)
  } catch (err) {
    setError(err.message)
    setIsLoading(false)
  }
}
```

### Replace mockResetPassword()

```javascript
const mockResetPassword = async (email) => {
  setIsLoading(true)
  setError(null)

  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    })

    if (error) throw error

    setIsLoading(false)
    return { success: true, message: `Reset link sent to ${email}` }
  } catch (err) {
    setError(err.message)
    setIsLoading(false)
  }
}
```

### Add Logout

```javascript
const logout = async () => {
  try {
    await supabase.auth.signOut()
    setIsAuthenticated(false)
    setCurrentUser({
      id: null,
      email: null,
      full_name: null,
      user_role: null,
      is_verified: false,
      is_active: true,
    })
  } catch (err) {
    setError(err.message)
  }
}
```

### Add Session Recovery

```javascript
// Add useEffect to recover session on app load
useEffect(() => {
  const recoverSession = async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession()

    if (session) {
      const { data: userData } = await supabase
        .from('users')
        .select('*')
        .eq('id', session.user.id)
        .single()

      if (userData) {
        setIsAuthenticated(true)
        setCurrentUser({
          id: session.user.id,
          email: session.user.email,
          full_name: userData.full_name,
          user_role: userData.user_role,
          is_verified: userData.is_verified,
          is_active: userData.is_active,
        })
      }
    }
  }

  recoverSession()
}, [])
```

---

## 🔐 Security Best Practices

### 1. Enable Email Verification

In your Supabase Dashboard:
- Go to Authentication → Providers → Email
- Enable "Confirm email" for sign ups
- Set confirmation email template

### 2. Configure Password Reset

- Set "Allow password resets" to enabled
- Configure reset email template
- Set redirect URL for password reset

### 3. Row Level Security

Enable RLS on all tables:

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
```

### 4. Environment Variables

Never commit `.env.local` to version control:

```bash
# .gitignore
.env.local
.env*.local
```

### 5. CORS Configuration

In Supabase Dashboard → Authentication → URL Configuration:
- Add your frontend URL (e.g., `http://localhost:5173` for dev)
- Add production URL when deploying

---

## 🧪 Testing Integration

### Test 1: User Registration

```javascript
// In browser console
const { data, error } = await supabase.auth.signUp({
  email: 'test@example.com',
  password: 'testPassword123'
})
```

### Test 2: User Login

```javascript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'test@example.com',
  password: 'testPassword123'
})
```

### Test 3: Query User Profile

```javascript
const { data } = await supabase
  .from('users')
  .select('*')
  .eq('email', 'test@example.com')
```

---

## 🚀 Deployment

### Vercel Deployment

1. Push code to GitHub
2. Connect repository to Vercel
3. Add environment variables in Vercel dashboard:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
4. Deploy

### Netlify Deployment

1. Connect repository to Netlify
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Add environment variables in Netlify dashboard
5. Deploy

---

## 🐛 Troubleshooting

### Issue: "CORS error"
**Solution**: Add your domain to Supabase URL Configuration

### Issue: "Auth session not persisting"
**Solution**: Check if Supabase client is initialized before components mount

### Issue: "User profile not created"
**Solution**: Ensure RLS policies allow inserts. Check Supabase logs.

### Issue: "Email not received"
**Solution**: Check SMTP settings in Supabase. Verify email domain in authentication settings.

---

## 📚 Additional Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Supabase Database Documentation](https://supabase.com/docs/guides/database)
- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [React with Supabase](https://supabase.com/docs/guides/auth/auth-helpers/nextjs)

---

**Happy integrating! 🎉**
