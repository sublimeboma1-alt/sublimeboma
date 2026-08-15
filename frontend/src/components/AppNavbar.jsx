import { useEffect, useRef, useState } from 'react'

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
  const [openMenu, setOpenMenu] = useState('')
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
    setOpenMenu((current) => (current === label ? '' : label))
  }

  return (
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
              </button>
              {isOpen && (
                <div className="nav-submenu" role="menu">
                  <div className="submenu-title">{section.label}</div>
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
                </div>
              )}
            </div>
            )
          })}
        </nav>
      </div>
      <style>{`
        .app-navbar.top-nav {
          width: 100vw;
          max-width: 100vw;
          margin-right: calc(50% - 50vw);
          margin-left: calc(50% - 50vw);
          align-self: stretch;
          background: linear-gradient(115deg, #061b34 0%, #0a4962 50%, #0b827a 100%);
          border-bottom: 1px solid rgba(255, 255, 255, 0.16);
          box-shadow: 0 14px 34px rgba(5, 25, 44, 0.22);
          backdrop-filter: blur(18px) saturate(135%);
        }

        .app-navbar .top-nav-inner {
          width: 100%;
          max-width: none;
          min-height: 82px;
          margin: 0;
          padding: 0 clamp(18px, 4vw, 64px);
          grid-template-columns: minmax(220px, 1fr) auto minmax(220px, 1fr);
        }

        .app-navbar .brand-mark {
          width: 45px;
          height: 45px;
          border: 1px solid rgba(255, 255, 255, 0.32);
          border-radius: 15px;
          background: linear-gradient(145deg, #f7cf70, #e99b3d);
          color: #12334a;
          box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
        }

        .app-navbar .main-nav {
          gap: 2px;
          padding: 5px;
          border-color: rgba(255, 255, 255, 0.2);
          background: rgba(255, 255, 255, 0.11);
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16), 0 6px 16px rgba(0, 15, 30, 0.12);
        }

        .app-navbar .nav-menu > button {
          gap: 8px;
          padding: 0 14px;
          border: 1px solid transparent;
          transition: transform 160ms ease, background 160ms ease, color 160ms ease, box-shadow 160ms ease;
        }

        .app-navbar .nav-menu > button:hover { transform: translateY(-1px); background: rgba(255, 255, 255, 0.16); color: #fff; }

        .app-navbar .nav-menu > button:focus-visible { outline: 3px solid rgba(247, 207, 112, .65); outline-offset: 2px; }

        .app-navbar .nav-icon {
          color: #f7cf70;
          font-size: 12px;
        }

        .app-navbar .nav-menu > button.active .nav-icon,
        .app-navbar .nav-menu > button:hover .nav-icon {
          color: #0c756f;
        }

        .app-navbar .nav-menu > button.active,
        .app-navbar .nav-menu > button[aria-expanded='true'] { border-color: rgba(255,255,255,.45); }

        .app-navbar .nav-submenu {
          overflow: hidden;
          width: 248px;
          padding: 7px;
          border: 1px solid rgba(12, 90, 91, 0.18);
          border-radius: 16px;
          background: rgba(255,255,255,.98);
          box-shadow: 0 22px 48px rgba(8, 35, 56, 0.25);
          animation: app-navbar-menu-in 160ms ease-out;
        }

        .app-navbar .submenu-title {
          padding: 9px 10px 8px;
          color: #6b7a89;
          font-size: 11px;
          font-weight: 900;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .app-navbar .nav-submenu a,
        .app-navbar .nav-submenu button {
          border-radius: 9px;
        }

        .app-navbar .nav-submenu .danger-action {
          margin-top: 4px;
          color: #a32338;
          background: #fff4f5;
        }

        @keyframes app-navbar-menu-in {
          from { opacity: 0; transform: translate(-50%, -6px); }
          to { opacity: 1; transform: translate(-50%, 0); }
        }

        @media (max-width: 980px) {
          .app-navbar.top-nav {
            position: sticky;
            top: 0;
            right: auto;
            bottom: auto;
            left: auto;
          }

          .app-navbar .top-nav-inner {
            grid-template-columns: 1fr;
            gap: 8px;
            padding: 8px 12px 10px;
          }

          .app-navbar .brand-block {
            justify-self: center;
            display: none;
          }

          .app-navbar .main-nav {
            width: 100%;
            justify-content: flex-start;
            min-height: 54px;
            padding: 5px 6px;
            border-radius: 16px;
            scroll-snap-type: x proximity;
          }

          .app-navbar .nav-submenu {
            position: fixed;
            top: 12px;
            right: 12px;
            bottom: auto;
            left: 12px;
            width: auto;
            max-height: min(420px, calc(100vh - 100px));
            transform: none;
            border-radius: 16px;
          }

          @keyframes app-navbar-menu-in {
            from { opacity: 0; transform: translateY(-6px); }
            to { opacity: 1; transform: translateY(0); }
          }
        }

        @media (max-width: 520px) {
          .app-navbar .nav-menu > button { min-width: 54px; padding: 0 10px; font-size: 11px; }
          .app-navbar .nav-icon { display: none; }
          .app-navbar .nav-menu { scroll-snap-align: start; }
        }
      `}</style>
    </header>
  )
}

export default AppNavbar
