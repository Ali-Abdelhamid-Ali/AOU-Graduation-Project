# 🔗 دليل ربط Supabase مع الفرونت إند

## الخطوات المطلوبة:

### 1. إنشاء ملف `.env.local`

أنشئ ملف `.env.local` في مجلد `frontend` وأضف:

```env
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

### 2. الحصول على بيانات Supabase

1. اذهب إلى [supabase.com](https://supabase.com)
2. أنشئ مشروع جديد أو استخدم مشروع موجود
3. اذهب إلى **Settings → API**
4. انسخ **Project URL** و **anon key**
5. الصقهم في ملف `.env.local`

### 3. إنشاء جدول Users في قاعدة البيانات

في Supabase SQL Editor، نفذ هذا الكود:

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  user_role TEXT CHECK (user_role IN ('doctor', 'patient')),
  is_verified BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can read own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can create own profile"
  ON users FOR INSERT
  WITH CHECK (auth.uid() = id);
```

### 4. تشغيل المشروع

```bash
npm run dev
```

## ✨ المميزات المضافة:

### Toast Notifications
- رسائل تظهر في منتصف الشاشة
- تختفي تلقائياً بعد ثانيتين
- حركة سلسة من الجنب
- أنواع مختلفة: success, error, warning, info

### ربط Supabase
- تسجيل الدخول
- إنشاء حساب جديد
- إعادة تعيين كلمة المرور
- حفظ بيانات المستخدم في قاعدة البيانات

## 📝 ملاحظات:

- إذا لم تكن Supabase مُعدة، النظام سيعمل في وضع Mock (محلي)
- الرسائل تظهر تلقائياً عند نجاح/فشل العمليات
- جميع الرسائل تظهر في منتصف الشاشة بحركة سلسة

