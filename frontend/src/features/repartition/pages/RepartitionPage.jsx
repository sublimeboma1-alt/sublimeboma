import { useEffect, useMemo, useState } from 'react'
import AppNavbar from '../../../components/AppNavbar'
import { defaultIdentity, fetchIdentity } from '../../../services/identityService'
import { useAuth } from '../../auth/context/authState'
import { fetchRepartitionDashboard, fetchRepartitionSettings, saveRepartitionSettings } from '../services/repartitionService'

const money = (value) => `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(value || 0)} FC`
const today = new Date().toISOString().slice(0, 10)

function RepartitionPage({ mode = 'dashboard' }) {
  const { user, signOut } = useAuth()
  const [identity, setIdentity] = useState(defaultIdentity)
  const [dashboard, setDashboard] = useState(null)
  const [settings, setSettings] = useState(null)
  const [selectedType, setSelectedType] = useState('')
  const [allocations, setAllocations] = useState([])
  const [openPayment, setOpenPayment] = useState(null)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [parameterName, setParameterName] = useState('')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [selectedParameter, setSelectedParameter] = useState('')
  const [dateStart, setDateStart] = useState(today)
  const [dateEnd, setDateEnd] = useState(today)
  const isSettings = mode === 'settings'

  const load = () => fetchRepartitionSettings().then(async (config) => {
    setSettings(config)
    const first = config.parametres?.find((item) => item.est_actif) || config.parametres?.[0]
    if (!selectedType && first) { setSelectedType(first.type_frais); setAllocations(first.allocations); setParameterName(first.nom) }
    const preferred = config.parametres?.find((item) => item.type_frais === 'minerval') || first
    const parameterId = selectedParameter || preferred?.id || ''
    setSelectedParameter(String(parameterId))
    const summary = await fetchRepartitionDashboard({ ...(parameterId ? { parametre_id: parameterId } : {}), date_debut: dateStart, date_fin: dateEnd })
    setDashboard(summary)
  }).catch((requestError) => setError(requestError.message || 'Chargement impossible.'))

  useEffect(() => { fetchIdentity().then(setIdentity).catch(() => {}); load() }, [])
  const total = useMemo(() => allocations.reduce((sum, item) => sum + Number(item.pourcentage || 0), 0), [allocations])

  function changeType(code) {
    const parameter = settings.parametres?.find((item) => item.type_frais === code && item.est_actif)
    const type = settings.types_frais.find((item) => item.code === code)
    setSelectedType(code); setAllocations(parameter?.allocations || settings.categories.map((item) => ({ ...item, categorie_id: item.id, pourcentage: 0 }))); setParameterName(parameter?.nom || `Repartition frais ${type?.libelle || ''}`); setNotice(''); setError('')
  }
  function changePercent(categoryId, value) {
    setAllocations((items) => items.map((item) => item.categorie_id === categoryId ? { ...item, pourcentage: value } : item))
  }
  async function saveSettings() {
    setNotice(''); setError('')
    if (Math.round(total * 100) !== 10000) { setError('Le total doit etre exactement egal a 100 %.'); return }
    setSaving(true)
    try {
      if (!parameterName.trim()) { setError('Donnez un nom au parametre.'); return }
      const result = await saveRepartitionSettings({ nom: parameterName.trim(), type_frais: selectedType, allocations: allocations.map((item) => ({ categorie_id: item.categorie_id, pourcentage: item.pourcentage })) })
      setNotice(`${result.paiements_repartis || 0} paiement(s) de l'annee scolaire active ont ete repartis.`)
      await load()
    } catch (requestError) { setError(requestError.message || 'Enregistrement impossible.') } finally { setSaving(false) }
  }
  function navigate(action) {
    if (action === 'fees.situation') window.location.hash = 'frais-situation'
    if (action === 'fees.years') window.location.hash = 'frais-annees'
    if (action === 'fees.tariffs') window.location.hash = 'frais-tarifs'
    if (action === 'fees.apply') window.location.hash = 'frais-appliquer'
    if (action === 'fees.statistics') window.location.hash = 'statistiques'
    if (action === 'finances.repartition') window.location.hash = 'repartition'
    if (action === 'exports.open') window.location.hash = 'exports'
    if (action === 'finances.depenses') window.location.hash = 'depenses'
    if (action === 'session.logout') signOut()
  }
  function openNewParameter() {
    const type = settings.types_frais[0]
    if (!type) return
    setSelectedType(type.code); setParameterName(`Repartition frais ${type.libelle}`); setAllocations(settings.categories.map((item) => ({ ...item, categorie_id: item.id, pourcentage: 0 }))); setIsCreateModalOpen(true)
  }
  function selectParameter(parameter) { setSelectedType(parameter.type_frais); setParameterName(parameter.nom); setAllocations(parameter.allocations); setIsCreateModalOpen(true) }
  async function filterDashboard(parameterId = selectedParameter, start = dateStart, end = dateEnd) {
    setSelectedParameter(parameterId)
    try { setDashboard(await fetchRepartitionDashboard({ ...(parameterId ? { parametre_id: parameterId } : {}), date_debut: start, date_fin: end })) } catch (requestError) { setError(requestError.message || 'Filtre impossible.') }
  }

  return <main className="app-shell fees-shell">
    <AppNavbar identity={identity} onNavigate={navigate} />
    <section className={`workspace repartition-workspace ${isSettings ? 'settings-mode' : 'dashboard-mode'}`}>
      <header className="repartition-hero">
        <div>{isSettings ? <><span>Administration · Parametres</span><h1>Parametres de repartition</h1><p>Definissez la cle appliquee automatiquement aux nouveaux paiements, selon leur type de frais.</p></> : <><span>Gestion financiere · Repartition</span><h1>Repartition des frais</h1><p>Consultez les montants que chaque categorie doit recevoir pour les paiements enregistres.</p></>}</div>
        <div className="repartition-user">{user?.username}</div>
      </header>
      {error && <p className="repartition-message error">{error}</p>}
      {notice && <p className="repartition-message success">{notice}</p>}
      {!dashboard || !settings ? <div className="loading-state">Chargement de la repartition...</div> : <>
        {!isSettings && <div className="repartition-filter"><label>Parametre de repartition<select value={selectedParameter} onChange={(event) => filterDashboard(event.target.value)}><option value="">Tous les parametres</option>{dashboard.parametres.map((parameter) => <option key={parameter.id} value={parameter.id}>{parameter.nom}</option>)}</select></label><label>Du<input type="date" value={dateStart} onChange={(event) => { setDateStart(event.target.value); filterDashboard(selectedParameter, event.target.value, dateEnd) }} /></label><label>Au<input type="date" value={dateEnd} onChange={(event) => { setDateEnd(event.target.value); filterDashboard(selectedParameter, dateStart, event.target.value) }} /></label><span>Annee scolaire active : <b>{dashboard.annee_scolaire?.annee || 'Non definie'}</b></span></div>}
        <section className="repartition-kpis">
          <article><span>Montant reparti</span><strong>{money(dashboard.total)}</strong><small>sur les paiements affiches</small></article>
          <article><span>Repartition du jour</span><strong>{money(dashboard.today_total)}</strong><small>paiements du jour</small></article>
          <article><span>Paiements ventiles</span><strong>{dashboard.payment_count}</strong><small>avec detail disponible</small></article>
        </section>
        <section className="repartition-grid">
          <article className="repartition-card settings-card">
            <div className="repartition-card-head"><div><span>Parametres</span><h2>Cle de repartition</h2></div><button className="parameter-add" type="button" onClick={openNewParameter}>+ Ajouter</button></div>
            <div className="parameter-list">{settings.parametres?.map((parameter) => <button type="button" key={parameter.id} onClick={() => selectParameter(parameter)}><span><b>{parameter.nom}</b><small>{parameter.type_frais_libelle}</small></span><em className={parameter.est_actif ? 'parameter-active' : ''}>{parameter.est_actif ? 'Actif' : 'Archive'}</em></button>)}</div>
            {isCreateModalOpen && <div className="parameter-modal-backdrop"><div className="parameter-modal"><div className="repartition-card-head"><div><span>Nouveau parametre</span><h2>Cle de repartition</h2></div><button className="modal-close" type="button" onClick={() => setIsCreateModalOpen(false)}>×</button></div><label className="repartition-select">Nom du parametre<input value={parameterName} placeholder="Ex. Repartition frais d'inscription 2026" onChange={(event) => setParameterName(event.target.value)} /></label>
            <label className="repartition-select">Type de frais<select value={selectedType} onChange={(event) => changeType(event.target.value)}>{settings.types_frais.map((type) => <option key={type.code} value={type.code}>{type.libelle}</option>)}</select></label>
            <div className="allocation-list">{allocations.map((item) => <div className="allocation-row" key={item.categorie_id}><i style={{ background: item.couleur }} /><label>{item.libelle}<input aria-label={`Pourcentage ${item.libelle}`} type="number" min="0" max="100" step="0.01" value={item.pourcentage} onChange={(event) => changePercent(item.categorie_id, event.target.value)} /></label><b>%</b></div>)}</div>
            <p className="settings-help">A l'enregistrement, la cle est appliquee a tous les paiements deja enregistres pour ce type de frais dans l'annee scolaire active, puis aux nouveaux encaissements.</p>
            <button className="save-repartition" type="button" disabled={saving} onClick={async () => { await saveSettings(); setIsCreateModalOpen(false) }}>{saving ? 'Enregistrement...' : 'Enregistrer le parametre'}</button></div></div>}
          </article>
          <article className="repartition-card summary-card"><div className="repartition-card-head"><div><span>Vue consolidee</span><h2>Repartition encaissee</h2></div></div>
            <div className="category-summary">{dashboard.by_category.map((item) => <article className="category-cell" key={item.id} style={{ '--category-color': item.couleur }}><div className="category-cell-top"><i /><span>{item.libelle}</span></div><strong>{money(item.amount)}</strong><div className="progress"><em style={{ width: `${item.percent}%` }} /></div><small>{item.percent} % du total reparti</small></article>)}</div>
          </article>
        </section>
        <section className="repartition-card payments-card"><div className="repartition-card-head"><div><span>Traçabilite</span><h2>Details par paiement</h2></div><small>Cliquez sur une ligne pour consulter sa ventilation.</small></div>
          <div className="payment-table"><div className="payment-row table-head"><span>Recu / date</span><span>Eleve et frais</span><span>Encaisse</span><span /></div>{dashboard.payments.length === 0 ? <p className="fees-empty">Aucun paiement reparti pour le moment.</p> : dashboard.payments.map((payment) => <button className="payment-row" key={payment.id} type="button" onClick={() => setOpenPayment(openPayment?.id === payment.id ? null : payment)}><span><b>{payment.reference}</b><small>{payment.date}</small></span><span><b>{payment.eleve}</b><small>{payment.type_frais}</small></span><strong>{money(payment.amount)}</strong><span className="chevron">{openPayment?.id === payment.id ? '−' : '+'}</span>{openPayment?.id === payment.id && <div className="payment-detail">{payment.allocations.map((allocation) => <div key={allocation.libelle}><i style={{ background: allocation.couleur }} />{allocation.libelle}<small>{allocation.pourcentage} %</small><b>{money(allocation.montant)}</b></div>)}</div>}</button>)}</div>
        </section>
      </>}
    </section>
  </main>
}

export default RepartitionPage
