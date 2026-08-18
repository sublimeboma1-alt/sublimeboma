import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { validerCodeJeton } from '../../../services/jetonService'

const JetonContext = createContext(null)

const STORAGE_KEY = 'sublime_jeton'

export function JetonProvider({ children }) {
  const [jeton, setJeton] = useState(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })
  const [isVerifying, setIsVerifying] = useState(false)
  const [erreur, setErreur] = useState('')

  useEffect(() => {
    if (jeton) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(jeton))
    } else {
      sessionStorage.removeItem(STORAGE_KEY)
    }
  }, [jeton])

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
  }, [])

  const estActif = !!jeton?.valide

  const value = {
    jeton,
    estActif,
    isVerifying,
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