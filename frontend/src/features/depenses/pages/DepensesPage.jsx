import { useEffect, useState } from 'react'
import AppNavbar from '../../../components/AppNavbar'
import { defaultIdentity, fetchIdentity } from '../../../services/identityService'
import { useAuth } from '../../auth/context/authState'
import { fetchCategories } from '../services/depenseService'

function DepensesPage() {
  const { user, signOut } = useAuth()
  const [identity, setIdentity] = useState(defaultIdentity)
  const [categories, setCategories] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => { fetchIdentity().then(setIdentity).catch(() => {}) }, [])
  useEffect(() => {
    let mounted = true
    fetchCategories()
      .then((rows) => { if (mounted) setCategories(rows) })
      .catch(() => {})
      .finally(() => { if (mounted) setIsLoading(false) })
    return () => { mounted = false }
  }, [])

  function navigate(action) {
    if (action === 'fees.dashboard') window.location.hash = 'frais'
    if (action === 'fees.statistics') window.location.hash = 'statistiques'
    if (action === 'fees.situation') window.location.hash = 'frais-situation'
    if (action === 'fees.years') window.location.hash = 'frais-annees'
    if (action === 'fees.tariffs') window.location.hash = 'frais-tarifs'
    if (action === 'fees.apply') window.location.hash = 'frais-appliquer'
    if (action === 'finances.depenses') window.location.hash = 'depenses'
    if (action === 'session.logout') signOut()
  }

  return (
    <main className="app-shell fees-shell">
      <AppNavbar identity={identity} onNavigate={navigate} />
      <section className="workspace fees-workspace">
        <header className="fees-header">
          <div>
            <p>Gestion financiere · Depenses</p>
            <h1>Depenses</h1>
            <span>Suivez les depenses de l etablissement.</span>
          </div>
          <div className="fees-header-actions">
            <span className="user-chip">{user?.username}</span>
          </div>
        </header>

        {isLoading ? <div className="loading-state">Chargement des depenses...</div> : (
          <section className="fees-panel">
            <div className="fees-panel-head">
              <div>
                <span>Categories</span>
                <h2>Categories de depenses</h2>
              </div>
            </div>
            <div className="fees-dossiers">
              {categories.length === 0 && <p className="fees-empty">Aucune categorie de depense pour le moment.</p>}
              {categories.map((cat) => (
                <article className="fees-dossier" key={cat.id}>
                  <div className="dossier-avatar">DP</div>
                  <div className="dossier-main">
                    <strong>{cat.nom}</strong>
                    <span>{cat.description || 'Aucune description'}</span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}
      </section>
    </main>
  )
}

export default DepensesPage
