import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { quitterModeFinance, validerCodeJeton } from '../../../services/jetonService'

const JetonContext = createContext(null)

const STORAGE_KEY = 'sublime_jeton'

function readStoredJeton() {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

export function JetonProvider({ children }) {
  const [jeton, setJeton] = useState(readStoredJeton)
  const [isJetonReady, setIsJetonReady] = useState(() => !readStoredJeton()?.code)
  const [isVerifying, setIsVerifying] = useState(false)
  const [erreur, setErreur] = useState('')

  useEffect(() => {
    if (jeton) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(jeton))
    } else {
      sessionStorage.removeItem(STORAGE_KEY)
    }
  }, [jeton])

  useEffect(() => {
    if (!jeton?.code) return
    let mounted = true
    validerCodeJeton(jeton.code)
      .then((data) => {
        if (mounted && data.valide) setJeton(data)
        if (mounted && !data.valide) setJeton(null)
      })
      .catch(() => { if (mounted) setJeton(null) })
      .finally(() => { if (mounted) setIsJetonReady(true) })
    return () => { mounted = false }
  }, [])

  const valider = useCallback(async (code) => {
    setIsVerifying(true)
    setErreur('')

    try {
      const data = await validerCodeJeton(code)
      if (data.valide) {
        setJeton(data)
        return { success: true, perimetre: data }
      } else {
        setErreur(data.message || 'Code jeton invalide.')
        return { success: false, message: data.message }
      }
    } catch (error) {
      const message = error.message || 'Impossible de valider le code jeton.'
      setErreur(message)
      return { success: false, message }
    } finally {
      setIsVerifying(false)
    }
  }, [])

  const effacer = useCallback(() => {
    setJeton(null)
    setErreur('')
    sessionStorage.removeItem(STORAGE_KEY)
    // Clear the server-side authorization too; a local storage change is not enough.
    quitterModeFinance().catch(() => {})
  }, [])

  const estActif = !!jeton?.valide

  const value = {
    jeton,
    estActif,
    isVerifying,
    isJetonReady,
    erreur,
    valider,
    effacer,
    setErreur,
  }

  return <JetonContext.Provider value={value}>{children}</JetonContext.Provider>
}

export function useJeton() {
  const context = useContext(JetonContext)
  if (!context) {
    throw new Error('useJeton doit etre utilise dans un JetonProvider')
  }
  return context
}
