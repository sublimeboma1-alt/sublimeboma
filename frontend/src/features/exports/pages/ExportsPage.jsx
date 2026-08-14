import { useEffect, useState } from 'react'
import AppNavbar from '../../../components/AppNavbar'
import { defaultIdentity, fetchIdentity } from '../../../services/identityService'
import { useAuth } from '../../auth/context/authState'
import { fetchElevesReferences } from '../../eleves/services/elevesService'
import { fetchClasses } from '../../eleves/services/elevesService'
import { fetchFeesReferences, exportSchoolData } from '../../frais-scolaires/services/fraisService'

const initialFilters = { annee_scolaire: '', niveau: '', classe_id: '', statut: '', sexe: '', type_frais: '', trimestre: '', search: '', date_debut: '', date_fin: '' }

function ExportsPage() {
  const { signOut } = useAuth()
  const [identity, setIdentity] = useState(defaultIdentity)
  const [scope, setScope] = useState('inscriptions')
  const [filters, setFilters] = useState(initialFilters)
  const [references, setReferences] = useState({ annees_scolaires: [], niveaux: [], statuts: [], sexes: [], types_frais: [], trimestres: [] })
  const [classes, setClasses] = useState([])
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState('')

  useEffect(() => {
    Promise.all([fetchIdentity(), fetchElevesReferences(), fetchFeesReferences(), fetchClasses()])
      .then(([school, eleveRefs, feesRefs, classRows]) => {
        setIdentity(school)
        const activeYearId = eleveRefs.annee_active_id || feesRefs.annee_active_id || ''
        setReferences({ ...eleveRefs, annees_scolaires: eleveRefs.annees_scolaires?.length ? eleveRefs.annees_scolaires : feesRefs.annees_scolaires || [], types_frais: feesRefs.types_frais || [], trimestres: feesRefs.trimestres || [] })
        setFilters((current) => ({ ...current, annee_scolaire: current.annee_scolaire || String(activeYearId) }))
        setClasses(classRows)
      })
      .catch(() => setError('Les filtres ne peuvent pas etre charges pour le moment.'))
  }, [])

  function navigate(action) {
    if (action === 'eleves.list') window.location.hash = 'eleves'
    if (action === 'fees.situation') window.location.hash = 'frais-situation'
    if (action === 'fees.statistics') window.location.hash = 'statistiques'
    if (action === 'fees.years') window.location.hash = 'frais-annees'
    if (action === 'fees.tariffs') window.location.hash = 'frais-tarifs'
    if (action === 'fees.apply') window.location.hash = 'frais-appliquer'
    if (action === 'finances.depenses') window.location.hash = 'depenses'
    if (action === 'exports.open') window.location.hash = 'exports'
    if (action === 'session.logout') signOut()
  }

  async function download(format) {
    setError('')
    setExporting(format)
    try {
      await exportSchoolData({ ...filters, scope, format })
    } catch (requestError) {
      setError(requestError.message || "L'export a echoue.")
    } finally {
      setExporting('')
    }
  }

  const availableClasses = classes.filter((item) => !filters.niveau || item.niveau_code === filters.niveau)
  const isFees = scope === 'frais'
  const activeYearId = String(references.annee_active_id || references.annees_scolaires.find((item) => item.est_active)?.id || '')
  const resetFilters = () => setFilters({ ...initialFilters, annee_scolaire: activeYearId })

  return (
    <div className="app-shell">
      <AppNavbar identity={identity} onNavigate={navigate} />
      <main className="workspace exports-workspace">
        <section className="exports-intro">
          <div><span>Centre de documents</span><h1>Exporter les donnees</h1><p>Choisissez les donnees et les filtres utiles. Le fichier est genere de maniere securisee par le serveur.</p></div>
          <div className="exports-format-note">XLSX et PDF<br /><small>Formats prets a partager</small></div>
        </section>

        <section className="exports-card">
          <div className="exports-kind">
            <button className={scope === 'inscriptions' ? 'active' : ''} onClick={() => { setScope('inscriptions'); resetFilters() }}><b>Inscriptions</b><span>Registre et informations des eleves</span></button>
            <button className={scope === 'frais' ? 'active' : ''} onClick={() => { setScope('frais'); resetFilters() }}><b>Frais et paiements</b><span>Historique des paiements enregistres</span></button>
          </div>

          <div className="exports-filter-head"><div><span>Selection</span><h2>Filtres d'export</h2></div><button className="exports-reset" onClick={resetFilters}>Reinitialiser</button></div>
          <div className="exports-filters">
            <label>Annee scolaire<select value={filters.annee_scolaire} onChange={(e) => setFilters({ ...filters, annee_scolaire: e.target.value })}><option value="">Toutes les annees</option>{references.annees_scolaires.map((item) => <option key={item.id} value={item.id}>{item.annee}</option>)}</select></label>
            <label>Niveau<select value={filters.niveau} onChange={(e) => setFilters({ ...filters, niveau: e.target.value, classe_id: '' })}><option value="">Tous les niveaux</option>{references.niveaux.map((item) => <option key={item.code} value={item.code}>{item.libelle}</option>)}</select></label>
            <label>Classe<select value={filters.classe_id} onChange={(e) => setFilters({ ...filters, classe_id: e.target.value })}><option value="">Toutes les classes</option>{availableClasses.map((item) => <option key={item.id} value={item.id}>{item.nom}</option>)}</select></label>
            {isFees ? <><label>Type de frais<select value={filters.type_frais} onChange={(e) => setFilters({ ...filters, type_frais: e.target.value })}><option value="">Tous les types</option>{references.types_frais.map((item) => <option key={item.code} value={item.code}>{item.libelle}</option>)}</select></label><label>Trimestre<select value={filters.trimestre} onChange={(e) => setFilters({ ...filters, trimestre: e.target.value })}><option value="">Tous les trimestres</option>{references.trimestres.map((item) => <option key={item.code} value={item.code}>{item.libelle}</option>)}</select></label><label>Statut paiement<select value={filters.statut} onChange={(e) => setFilters({ ...filters, statut: e.target.value })}><option value="">Tous les statuts</option><option value="valide">Valide</option><option value="annule">Annule</option></select></label></> : <label>Statut eleve<select value={filters.statut} onChange={(e) => setFilters({ ...filters, statut: e.target.value })}><option value="">Tous les statuts</option>{references.statuts.map((item) => <option key={item.code} value={item.code}>{item.libelle}</option>)}</select></label>}
            {!isFees && <label>Sexe<select value={filters.sexe} onChange={(e) => setFilters({ ...filters, sexe: e.target.value })}><option value="">Tous</option>{references.sexes.map((item) => <option key={item.code} value={item.code}>{item.libelle}</option>)}</select></label>}
            <label>Du<input type="date" value={filters.date_debut} onChange={(e) => setFilters({ ...filters, date_debut: e.target.value })} /></label>
            <label>Au<input type="date" value={filters.date_fin} onChange={(e) => setFilters({ ...filters, date_fin: e.target.value })} /></label>
            <label className="exports-search">Recherche<input placeholder="Nom ou matricule" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} /></label>
          </div>
          {error && <p className="exports-error">{error}</p>}
          <div className="exports-actions"><div><strong>{isFees ? 'Rapport des paiements' : 'Registre des inscriptions'}</strong><span>Les filtres selectionnes seront appliques au document.</span></div><button className="export-pdf" disabled={Boolean(exporting)} onClick={() => download('pdf')}>{exporting === 'pdf' ? 'Preparation...' : 'Exporter en PDF'}</button><button className="export-xlsx" disabled={Boolean(exporting)} onClick={() => download('xlsx')}>{exporting === 'xlsx' ? 'Preparation...' : 'Exporter en XLSX'}</button></div>
        </section>
      </main>
    </div>
  )
}

export default ExportsPage
