'use client'

import { useAuth } from './providers/SupabaseAuthProvider'
import Sidebar from '../components/Sidebar'
import AuthDebugger from '../components/AuthDebugger'
import { useState } from 'react'
import { supabase } from '../lib/supabase'

export default function Home() {
  const { session } = useAuth()

  if (!session) {
    return <LoginForm />
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1>Willkommen zu PPM SaaS</h1>
        {/* Füge Links zu Dashboards etc. hinzu */}
      </main>
    </div>
  )
}

function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignup, setIsSignup] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    console.log('Starting authentication process...')

    try {
      // Try Supabase JS SDK first (more reliable for auth)
      console.log('Attempting Supabase JS authentication...')
      
      const { data, error } = isSignup
        ? await supabase.auth.signUp({ 
            email, 
            password,
            options: {
              emailRedirectTo: window.location.origin
            }
          })
        : await supabase.auth.signInWithPassword({ email, password })
      
      if (error) {
        console.error('Supabase JS Auth error:', error)
        throw new Error(error.message)
      } else {
        console.log('Supabase JS Auth successful:', data)
        if (isSignup) {
          setError('Account created successfully! Please check your email to confirm.')
        } else {
          setError('Login successful! Redirecting...')
          setTimeout(() => {
            window.location.reload()
          }, 1500)
        }
        setLoading(false)
        return
      }
    } catch (err: unknown) {
      console.error('Supabase JS failed, trying direct API fallback:', err)
      
      // Fallback to direct API
      try {
        const { directSignUp, directSignIn } = await import('../lib/auth-direct')
        
        console.log('Using direct API authentication...')
        
        const result = isSignup 
          ? await directSignUp(email, password)
          : await directSignIn(email, password)
        
        if (result.success) {
          console.log('Direct API auth successful:', result.data)
          setError(result.message || (isSignup ? 'Account created successfully!' : 'Login successful!'))
          
          if (!isSignup && result.data) {
            setTimeout(() => {
              window.location.reload()
            }, 1500)
          }
        } else {
          console.error('Direct API auth failed:', result.error)
          setError(`Authentication failed: ${result.error}`)
        }
      } catch (directError: unknown) {
        const originalMessage = err instanceof Error ? err.message : 'Unknown error'
        const directMessage = directError instanceof Error ? directError.message : 'Unknown error'
        setError(`All authentication methods failed. Supabase JS: ${originalMessage}. Direct API: ${directMessage}`)
      }
    }
    
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {isSignup ? 'Create your account' : 'Sign in to your account'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            AI-Powered Project Portfolio Management
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleAuth}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Enter your email"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete={isSignup ? 'new-password' : 'current-password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Enter your password"
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                isSignup ? 'Sign Up' : 'Sign In'
              )}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setIsSignup(!isSignup)}
              className="text-blue-600 hover:text-blue-500 text-sm"
            >
              {isSignup ? 'Already have an account? Sign in' : 'Need an account? Sign up'}
            </button>
            
            {!isSignup && (
              <a
                href="/forgot-password"
                className="text-blue-600 hover:text-blue-500 text-sm"
              >
                Forgot password?
              </a>
            )}
          </div>
        </form>

        {/* Debug component - remove in production */}
        <AuthDebugger />
      </div>
    </div>
  )
}