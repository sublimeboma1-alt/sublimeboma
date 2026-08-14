import { useEffect, useMemo, useState } from 'react'
import { fetchSession, loginUser, logoutUser } from '../services/authService'
import { AuthContext } from './authState'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadSession() {
      try {
        const session = await fetchSession()
        if (isMounted) {
          setUser(session.user)
        }
      } catch {
        if (isMounted) {
          setUser(null)
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadSession()

    return () => {
      isMounted = false
    }
  }, [])

  async function signIn(credentials) {
    setError('')
    const session = await loginUser(credentials)
    setUser(session.user)
    return session.user
  }

  async function signOut() {
    await logoutUser()
    setUser(null)
  }

  const value = useMemo(
    () => ({
      user,
      error,
      isLoading,
      isAuthenticated: Boolean(user),
      setError,
      signIn,
      signOut,
    }),
    [error, isLoading, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
