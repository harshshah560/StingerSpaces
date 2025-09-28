# Authentication System

This folder contains the modular authentication system for the StingerSpaces apartment search platform.

## File Structure

```
auth/
├── js/
│   ├── auth-config.js      # Supabase configuration and AuthManager class
│   ├── auth-ui.js          # Login/signup UI logic and form handling
│   └── main-app-auth.js    # Main app authentication integration
├── css/
│   └── auth-styles.css     # Authentication page styles
└── README.md               # This file
```

## Setup Instructions

### 1. Supabase Configuration

The authentication system uses Supabase for user management. The configuration is already set up in `auth-config.js` with:
- Project URL: `https://dbkmzqknpvzumthytnyw.supabase.co`
- Anon key: Already configured

### 2. Database Setup

Run the following SQL in your Supabase SQL editor to set up the required tables:

```sql
-- Enable Row Level Security (RLS) on auth.users is already enabled by default

-- Create profiles table for additional user data
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on profiles table
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create policies for profiles table
CREATE POLICY "Users can view their own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile" ON public.profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Create apartment reviews table (for future use)
CREATE TABLE IF NOT EXISTS public.apartment_reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    apartment_name TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5) NOT NULL,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on reviews table
ALTER TABLE public.apartment_reviews ENABLE ROW LEVEL SECURITY;

-- Create policies for reviews table
CREATE POLICY "Anyone can view reviews" ON public.apartment_reviews
    FOR SELECT USING (true);

CREATE POLICY "Users can create their own reviews" ON public.apartment_reviews
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own reviews" ON public.apartment_reviews
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own reviews" ON public.apartment_reviews
    FOR DELETE USING (auth.uid() = user_id);

-- Create function to automatically create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger to call the function
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

### 3. Integration

The authentication system is already integrated into:

- **Landing Page** (`/frontend/landing.html`): Login/signup forms
- **Main App** (`/frontend/index.html`): Authentication state and user menu

### 4. Usage

#### For Login/Signup Page:
```html
<!-- Include Supabase SDK -->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>

<!-- Include auth scripts -->
<script src="auth/js/auth-config.js"></script>
<script src="auth/js/auth-ui.js"></script>
```

#### For Main App:
```html
<!-- Include Supabase SDK -->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>

<!-- Include auth scripts -->
<script src="auth/js/auth-config.js"></script>
<script src="auth/js/main-app-auth.js"></script>
```

### 5. AuthManager API

The `AuthManager` class provides the following methods:

```javascript
// Check if user is authenticated
authManager.isAuthenticated()

// Get current user
authManager.getCurrentUser()

// Sign up new user
await authManager.signUp(email, password, userData)

// Sign in existing user
await authManager.signIn(email, password)

// Sign out current user
await authManager.signOut()
```

### 6. Security Notes

- **Anon Key**: Safe for frontend use, respects Row Level Security
- **Service Role Key**: Never use in frontend code, bypasses all security
- **RLS**: Always enabled on all tables with appropriate policies
- **Data Validation**: All forms include client-side and server-side validation

### 7. Development

To test the authentication system:

1. Start your local server: `python3 -m http.server 8000`
2. Navigate to `http://localhost:8000/landing.html`
3. Try signing up with a new account
4. Check your Supabase dashboard to see the new user
5. Try logging in and navigating to the main app

### 8. Troubleshooting

- **"Invalid API key"**: Check that the anon key is correctly set in `auth-config.js`
- **"User not found"**: Make sure the user is confirmed (check email or disable email confirmation in Supabase settings)
- **"Access denied"**: Check Row Level Security policies in Supabase
- **"CORS errors"**: Make sure you're accessing via HTTP server, not file:// protocol