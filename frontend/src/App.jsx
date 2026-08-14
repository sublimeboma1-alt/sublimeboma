import { useEffect, useState } from 'react'
import ElevesPage from './features/eleves/pages/ElevesPage'
import FraisScolairesPage from './features/frais-scolaires/pages/FraisScolairesPage'
import EleveFraisDetailPage from './features/frais-scolaires/pages/EleveFraisDetailPage'
import DepensesPage from './features/depenses/pages/DepensesPage'
import ExportsPage from './features/exports/pages/ExportsPage'
import { AuthProvider } from './features/auth/context/AuthProvider'
import { useAuth } from './features/auth/context/authState'
import LoginPage from './features/auth/pages/LoginPage'
import './App.css'

function ProtectedApp() {
  const { isAuthenticated, isLoading } = useAuth()
  const [route, setRoute] = useState(() => window.location.hash.slice(1) || 'eleves')

  useEffect(() => {
    if (isAuthenticated && !window.location.hash) {
      window.location.hash = 'eleves'
    }
  }, [isAuthenticated])

  useEffect(() => {
    const syncRoute = () => setRoute(window.location.hash.slice(1) || 'eleves')
    window.addEventListener('hashchange', syncRoute)
    return () => window.removeEventListener('hashchange', syncRoute)
  }, [])

  if (isLoading) {
    return <div className="boot-screen">Verification de la session</div>
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  const feeTabs = { paiements: 'statistics', statistiques: 'statistics', 'frais-situation': 'dossiers', 'frais-annees': 'years', 'frais-tarifs': 'tariffs', 'frais-appliquer': 'apply' }
  if (route === 'depenses') return <DepensesPage />
  if (route === 'exports') return <ExportsPage />
  if (route.startsWith('frais-situation/')) {
    const eleveId = Number(route.split('/')[1] || 0)
    return <EleveFraisDetailPage eleveId={eleveId} onBack={() => { window.location.hash = 'frais-situation' }} />
  }
  if (route.startsWith('frais') || route === 'paiements' || route === 'statistiques') return <FraisScolairesPage initialTab={feeTabs[route] || 'overview'} />
  return <ElevesPage />
}

function App() {
  return (
    <AuthProvider>
      <ProtectedApp />
    </AuthProvider>
  )
}

export default App
