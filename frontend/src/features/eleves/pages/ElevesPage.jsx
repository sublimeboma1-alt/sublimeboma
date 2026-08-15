import { useEffect, useMemo, useRef, useState } from 'react'
import EleveDetailModal from '../components/EleveDetailModal'
import EleveFormModal from '../components/EleveFormModal'
import ElevesStats from '../components/ElevesStats'
import ElevesTable from '../components/ElevesTable'
import ElevesToolbar from '../components/ElevesToolbar'
import {
  createEleve,
  deleteEleve,
  fetchClasses,
  fetchEleves,
  fetchElevesReferences,
  updateEleve,
} from '../services/elevesService'
import { useAuth } from '../../auth/context/authState'
import AppNavbar from '../../../components/AppNavbar'
import { defaultIdentity, fetchIdentity } from '../../../services/identityService'

const initialFilters = {
  search: '',
  annee_scolaire: '',
  niveau: '',
  classe_id: '',
  statut: '',
  sexe: '',
}

function matchesSearch(eleve, search) {
  const value = search.trim().toLowerCase()
  if (!value) {
    return true
  }

  return [eleve.matricule, eleve.nom, eleve.post_nom, eleve.prenom, eleve.telephone]
    .filter(Boolean)
    .some((field) => field.toLowerCase().includes(value))
}

function ElevesPage({ openCreate = false }) {
  const { user, signOut } = useAuth()
  const [eleves, setEleves] = useState([])
  const [classes, setClasses] = useState([])
  const [filters, setFilters] = useState(initialFilters)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [references, setReferences] = useState({ annees_scolaires: [], sexes: [], statuts: [] })
  const [identity, setIdentity] = useState(defaultIdentity)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingEleve, setEditingEleve] = useState(null)
  const [selectedEleve, setSelectedEleve] = useState(null)
  const toolbarRef = useRef(null)
  const tableRef = useRef(null)

  useEffect(() => { setIsCreateOpen(openCreate) }, [openCreate])

  useEffect(() => {
    let isMounted = true

    async function loadData() {
      setIsLoading(true)
      setLoadError('')

      try {
        const [elevesData, classesData, referencesData, identityData] = await Promise.all([
          fetchEleves(),
          fetchClasses(),
          fetchElevesReferences(),
          fetchIdentity(),
        ])

        if (isMounted) {
          setEleves(elevesData)
          setClasses(classesData)
          setReferences(referencesData)
          setIdentity(identityData)
        }
      } catch (error) {
        if (isMounted) {
          setEleves([])
          setClasses([])
          setLoadError(error.message || 'Impossible de charger les donnees du backend.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadData()

    return () => {
      isMounted = false
    }
  }, [])

  const filteredEleves = useMemo(() => {
    return eleves.filter((eleve) => {
      const sameClasse = filters.classe_id ? String(eleve.classe_id) === String(filters.classe_id) : true
      const sameAnnee = filters.annee_scolaire && filters.annee_scolaire !== 'toutes'
        ? String(eleve.annee_scolaire_id) === String(filters.annee_scolaire)
        : true
      const sameNiveau = filters.niveau ? eleve.niveau_code === filters.niveau : true
      const sameStatut = filters.statut ? eleve.statut === filters.statut : true
      const sameSexe = filters.sexe ? eleve.sexe === filters.sexe : true
      return sameClasse && sameAnnee && sameNiveau && sameStatut && sameSexe && matchesSearch(eleve, filters.search)
    })
  }, [eleves, filters])

  async function loadElevesWithFilters(nextFilters, errorMessage = 'Impossible de charger les eleves avec ces filtres.') {
    setIsLoading(true)
    setLoadError('')

    try {
      const elevesData = await fetchEleves(nextFilters)
      setEleves(elevesData)
    } catch (error) {
      setEleves([])
      setLoadError(error.message || errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  async function handleFilterChange(name, value) {
    const nextFilters = {
      ...filters,
      [name]: value,
      ...(name === 'niveau' ? { classe_id: '' } : {}),
    }

    setFilters(nextFilters)
    await loadElevesWithFilters(nextFilters)
  }

  async function reloadEleves() {
    const elevesData = await fetchEleves({ annee_scolaire: filters.annee_scolaire })
    setEleves(elevesData)
  }

  async function handleCreateEleve(payload) {
    setIsSaving(true)
    setLoadError('')

    try {
      await createEleve(cleanElevePayload(payload))
      await reloadEleves()
      setIsCreateOpen(false)
      window.location.hash = 'eleves'
    } catch (error) {
      setLoadError(error.message || "Impossible d'ajouter l'eleve.")
    } finally {
      setIsSaving(false)
    }
  }

  function cleanElevePayload(payload) {
    const cleanPayload = { ...payload }
    if (!cleanPayload.date_inscription) {
      delete cleanPayload.date_inscription
    }
    if (!cleanPayload.date_naissance) {
      delete cleanPayload.date_naissance
    }
    if (!cleanPayload.classe_id) {
      cleanPayload.classe_id = ''
    }
    return cleanPayload
  }

  async function handleUpdateEleve(payload) {
    if (!editingEleve) {
      return
    }

    setIsSaving(true)
    setLoadError('')

    try {
      const updatedEleve = await updateEleve(editingEleve.id, cleanElevePayload(payload))
      setEleves((current) => current.map((eleve) => (eleve.id === updatedEleve.id ? updatedEleve : eleve)))
      setEditingEleve(null)
      if (selectedEleve?.id === updatedEleve.id) {
        setSelectedEleve(updatedEleve)
      }
    } catch (error) {
      setLoadError(error.message || "Impossible de modifier l'eleve.")
    } finally {
      setIsSaving(false)
    }
  }

  async function handleDeleteEleve(eleve) {
    const confirmed = window.confirm(`Supprimer le dossier de ${eleve.nom_complet || eleve.matricule} ?`)
    if (!confirmed) {
      return
    }

    setLoadError('')

    try {
      await deleteEleve(eleve.id)
      setEleves((current) => current.filter((item) => item.id !== eleve.id))
      if (selectedEleve?.id === eleve.id) {
        setSelectedEleve(null)
      }
    } catch (error) {
      setLoadError(error.message || "Impossible de supprimer l'eleve.")
    }
  }

  function scrollToElement(ref) {
    window.setTimeout(() => {
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 0)
  }

  function handleNavbarAction(action) {
    if (action === 'eleves.list') {
      setActiveView('list')
      setFilters(initialFilters)
      loadElevesWithFilters(initialFilters, 'Impossible de recharger la liste des eleves.')
      scrollToElement(tableRef)
      return
    }

    if (action === 'eleves.create') {
      setIsCreateOpen(true)
      return
    }

    if (action === 'eleves.classes') {
      setActiveView('list')
      setFilters((current) => ({ ...current, classe_id: '' }))
      scrollToElement(toolbarRef)
      return
    }

    if (action === 'fees.dashboard') {
      window.location.hash = 'frais'
      return
    }

    if (action === 'fees.statistics') {
      window.location.hash = 'statistiques'
      return
    }

    if (action === 'fees.situation') {
      window.location.hash = 'frais-situation'
      return
    }

    if (action === 'fees.years') {
      window.location.hash = 'frais-annees'
      return
    }

    if (action === 'fees.tariffs') {
      window.location.hash = 'frais-tarifs'
      return
    }

    if (action === 'fees.apply') {
      window.location.hash = 'frais-appliquer'
      return
    }

    if (action === 'finances.depenses') {
      window.location.hash = 'depenses'
      return
    }

    if (action === 'exports.open') {
      window.location.hash = 'exports'
      return
    }

    if (action === 'eleves.print') {
      window.print()
      return
    }

    if (action === 'session.logout') {
      signOut()
    }
  }

  return (
    <main className="app-shell">
      <AppNavbar identity={identity} onNavigate={handleNavbarAction} />

      <section className="workspace" id="eleves">
        <header className="page-header">
          <div>
            <p>{identity.nom}</p>
            <h1>Eleves</h1>
          </div>
          <div className="header-actions">
            <span className="user-chip">{user?.username}</span>
          </div>
        </header>

        <ElevesStats eleves={filteredEleves} />
        <div ref={toolbarRef}>
          <ElevesToolbar
            filters={filters}
            classes={classes}
            references={references}
            onFilterChange={handleFilterChange}
          />
        </div>

        {loadError && <div className="error-state">{loadError}</div>}

        {isLoading ? (
          <div className="loading-state">Chargement des eleves</div>
        ) : (
          <div ref={tableRef}>
            <ElevesTable
              eleves={filteredEleves}
              onDelete={handleDeleteEleve}
              onEdit={setEditingEleve}
              onViewDetails={setSelectedEleve}
            />
          </div>
        )}
      </section>

      {isCreateOpen && (
        <EleveFormModal
          classes={classes}
          references={references}
          isOpen
          isSaving={isSaving}
          onClose={() => { setIsCreateOpen(false); window.location.hash = 'eleves' }}
          onSubmit={handleCreateEleve}
        />
      )}
      {editingEleve && (
        <EleveFormModal
          classes={classes}
          eleve={editingEleve}
          references={references}
          isOpen
          isSaving={isSaving}
          mode="edit"
          onClose={() => setEditingEleve(null)}
          onSubmit={handleUpdateEleve}
        />
      )}
      <EleveDetailModal eleve={selectedEleve} onClose={() => setSelectedEleve(null)} />
    </main>
  )
}

export default ElevesPage
