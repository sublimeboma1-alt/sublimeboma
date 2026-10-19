import { useEffect, useRef, useState } from 'react'
import { useJeton } from '../features/auth/context/JetonContext'
import JetonModal from '../features/auth/components/JetonModal'
import { useAuth } from '../features/auth/context/authState'
import { apiClient } from '../services/apiClient'

const navSections = [
  {
    label: 'Eleves',
    icon: '●',
    active: true,
    items: [
      { label: 'Liste des eleves', href: '#eleves' },
      { label: 'Nouvelle inscription', href: '#eleves/nouveau' },
    ],
  },
  {
    label: 'Scolarite',
    icon: '▦',
    items: [
      { label: 'Classes', href: '#classes' },
      { label: 'Annees scolaires', href: '#annees-scolaires' },
      { label: 'Rapports eleves', href: '#rapports' },
      { label: 'Exports', action: 'exports.open' },
    ],
  },
  {
    label: 'Finances',
    icon: '¤',
    requiresJeton: true,
    items: [
      { label: 'Situation eleves', href: '#frais-situation' },
      { label: 'Annee scolaire', href: '#frais-annees' },
      { label: 'Configurer tarifs', href: '#frais-tarifs' },
      { label: 'Appliquer tarifs', href: '#frais-appliquer' },
      { label: 'Statistiques', href: '#statistiques' },
      { label: 'Repartition', href: '#repartition' },
      { label: 'Exports', href: '#exports' },
      { label: 'Depenses', href: '#depenses' },
    ],
  },
  {
    label: 'Administration',
    icon: '⚙',
    items: [
      { label: 'Reglements scolaires', href: '#regularisations' },
      { label: 'Generer un jeton admin', action: 'regularisations.generate', staffOnly: true },
      { label: 'Quitter', action: 'session.logout', isDanger: true },
    ],
  },
]

function AppNavbar({ identity, onNavigate }) {
  const { estActif, jeton, effacer } = useJeton()
  const { user } = useAuth()
  const [openMenu, setOpenMenu] = useState('')
  const [jetonModalOpen, setJetonModalOpen] = useState(false)
  const [generatedRegularisationCode, setGeneratedRegularisationCode] = useState('')
  const [regularisationTokenError, setRegularisationTokenError] = useState('')
  const navRef = useRef(null)

  useEffect(() => {
    function handleDocumentClick(event) {
      if (navRef.current && !navRef.current.contains(event.target)) {
        setOpenMenu('')
      }
    }

    function handleEscape(event) {
      if (event.key === 'Escape') {
        setOpenMenu('')
      }
    }

    document.addEventListener('mousedown', handleDocumentClick)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handleDocumentClick)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [])

  async function generateRegularisationToken() {
    setRegularisationTokenError('')
    try {
      const result = await apiClient.post('/regularisations/api/jeton/creer/', {})
      setRegularisationTokenError('')
      setGeneratedRegularisationCode(result.code)
      try { sessionStorage.setItem('regularisations_jeton_generated_code', result.code) } catch {}
      window.dispatchEvent(new CustomEvent('regularisations:token-created', { detail: result.code }))
    } catch (error) {
      setRegularisationTokenError(error.message || 'Impossible de generer le jeton.')
    }
  }
  function toggleMenu(label) {
    if (label === 'Finances' && !estActif) {
      setJetonModalOpen(true)
      return
    }
    setOpenMenu((current) => (current === label ? '' : label))
  }

  return (
    <>
      <header className="top-nav app-navbar">
        <div className="top-nav-inner">
          <div className="brand-block">
            <div className="brand-mark">{identity?.sigle || 'CS'}</div>
            <div>
              <strong>{identity?.nom || 'Complexe Scolaire Sublime'}</strong>
              <span>{identity?.espace || 'Administration'}</span>
            </div>
          </div>

          <nav className="main-nav" aria-label="Navigation principale" ref={navRef}>
            {navSections.map((section) => {
              const isOpen = openMenu === section.label
              const isLocked = section.requiresJeton && !estActif

              return (
                <div className="nav-menu" key={section.label}>
                  <button
                    type="button"
                    className={section.active || isOpen ? 'active' : ''}
                    aria-expanded={isOpen}
                    aria-haspopup="menu"
                    onClick={() => toggleMenu(section.label)}
                  >
                    <span className="nav-icon" aria-hidden="true">{section.icon}</span>
                    {section.label}
                    {isLocked && <span className="nav-lock" aria-hidden="true">🔒</span>}
                    {section.requiresJeton && estActif && <span className="nav-unlocked" aria-hidden="true">✓</span>}
                  </button>
                  {isOpen && !isLocked && (
                    <div className="nav-submenu" role="menu">
                      <div className="submenu-title">
                        {section.label}
                        {section.requiresJeton && estActif && jeton && (
                          <span className="jeton-badge">
                            {jeton.niveau_libelle || jeton.classe_nom || jeton.type_frais_libelle || 'Acces general'}
                          </span>
                        )}
                      </div>
                      {section.items.filter((item) => !item.staffOnly || user?.is_staff).map((item) => {
                        if (item.action) {
                          return (
                            <button
                              key={item.action}
                              type="button"
                              role="menuitem"
                              className={item.isDanger ? 'danger-action' : undefined}
                              onClick={() => {
                                if (item.action === 'regularisations.generate') generateRegularisationToken()
                                else onNavigate?.(item.action)
                                setOpenMenu('')
                              }}
                            >
                              {item.label}
                            </button>
                          )
                        }

                        return (
                          <a key={item.href} href={item.href} role="menuitem" onClick={() => setOpenMenu('')}>
                            {item.label}
                          </a>
                        )
                      })}
                      {section.requiresJeton && estActif && (
                        <button
                          type="button"
                          role="menuitem"
                          className="danger-action jeton-quit-btn"
                          onClick={() => {
                            effacer()
                            setOpenMenu('')
                            window.location.hash = 'eleves'
                          }}
                        >
                          Quitter le mode finance
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </nav>
          <button className="navbar-logout" type="button" onClick={() => onNavigate?.('session.logout')}>
            Déconnexion
          </button>
        </div>
      </header>
      {(generatedRegularisationCode || regularisationTokenError) && (
        <div className="parameter-modal-backdrop" role="presentation">
          <section className="parameter-modal" role="dialog" aria-modal="true" aria-labelledby="regularisation-token-title">
            <h2 id="regularisation-token-title">{generatedRegularisationCode ? 'Jeton de regularisation genere' : 'Generation du jeton impossible'}</h2>
            <p>Copiez et partagez ce code avec les personnes autorisees.</p>
            {generatedRegularisationCode && <p><code>{generatedRegularisationCode}</code></p>}
            {regularisationTokenError && <p role="alert">{regularisationTokenError}</p>}
            <div className="modal-actions"><button type="button" disabled={!generatedRegularisationCode} onClick={() => navigator.clipboard?.writeText(generatedRegularisationCode)}>Copier le code</button><button type="button" onClick={() => { setGeneratedRegularisationCode(''); setRegularisationTokenError('') }}>Fermer</button></div>
          </section>
        </div>
      )}`r`n      <JetonModal
        isOpen={jetonModalOpen}
        onClose={() => setJetonModalOpen(false)}
        onSuccess={() => {
          setJetonModalOpen(false)
          setOpenMenu('Finances')
        }}
      />
    </>
  )
}

export default AppNavbar
