import { useEffect, useRef, useState } from 'react'
import { useJeton } from '../features/auth/context/JetonContext'
import JetonModal from '../features/auth/components/JetonModal'

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
      { label: 'Etablissement', href: '#etablissement' },
      { label: 'Utilisateurs', href: '#utilisateurs' },
      { label: 'Parametres', href: '#parametres' },
      { label: 'Quitter', action: 'session.logout', isDanger: true },
    ],
  },
]

function AppNavbar({ identity, onNavigate }) {
  const { estActif, jeton, effacer } = useJeton()
  const [openMenu, setOpenMenu] = useState('')
  const [jetonModalOpen, setJetonModalOpen] = useState(false)
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
                            {jeton.eleve_nom || jeton.classe_nom || jeton.type_frais_libelle || 'Acces general'}
                          </span>
                        )}
                      </div>
                      {section.items.map((item) => {
                        if (item.action) {
                          return (
                            <button
                              key={item.action}
                              type="button"
                              role="menuitem"
                              className={item.isDanger ? 'danger-action' : undefined}
                              onClick={() => {
                                onNavigate?.(item.action)
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
        </div>
      </header>
      <JetonModal
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