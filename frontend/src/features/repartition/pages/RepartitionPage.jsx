import { useEffect, useMemo, useState } from 'react'
import AppNavbar from '../../../components/AppNavbar'
import { defaultIdentity, fetchIdentity } from '../../../services/identityService'
import { useAuth } from '../../auth/context/authState'
import { fetchRepartitionDashboard, fetchRepartitionSettings, saveRepartitionSettings } from '../services/repartitionService'

const money = (value) => `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(value || 0)} FC`
const today = new Date().toISOString().slice(0, 10)
const defaultAllocations = (categories = []) => categories.map((item) => ({
  ...item,
  categorie_id: item.id,
  // Le fonctionnement interne démarre volontairement à 0 %.
  pourcentage: 0,
}))

function RepartitionPage({ mode = 'dashboard' }) {
  const { user, signOut } = useAuth()
  const [identity, setIdentity] = useState(defaultIdentity)
  const [dashboard, setDashboard] = useState(null)
  const [settings, setSettings] = useState(null)
  const [selectedType, setSelectedType] = useState('')
  const [allocations, setAllocations] = useState([])
  const [openPayment, setOpenPayment] = useState(null)
  const [isDimeModalOpen, setIsDimeModalOpen] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [parameterName, setParameterName] = useState('')
  const [acceptsDime, setAcceptsDime] = useState(false)
  const [dimePercent, setDimePercent] = useState('10')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [selectedParameter, setSelectedParameter] = useState('')
  const [dateStart, setDateStart] = useState(today)
  const [dateEnd, setDateEnd] = useState(today)
  const isSettings = mode === 'settings'

  const load = () => fetchRepartitionSettings().then(async (config) => {
    setSettings(config)
    const first = config.parametres?.find((item) => item.est_actif) || config.parametres?.[0]
    if (!selectedType && first) { setSelectedType(first.type_frais); setAllocations(first.allocations); setParameterName(first.nom); setAcceptsDime(first.accepte_dime); setDimePercent(String(first.pourcentage_dime ?? 10)) }
    const preferred = config.parametres?.find((item) => item.type_frais === 'minerval') || first
    const parameterId = selectedParameter || preferred?.id || ''
    setSelectedParameter(String(parameterId))
    const summary = await fetchRepartitionDashboard({ ...(parameterId ? { parametre_id: parameterId } : {}), date_debut: dateStart, date_fin: dateEnd })
    setDashboard(summary)
  }).catch((requestError) => setError(requestError.message || 'Chargement impossible.'))

  useEffect(() => { fetchIdentity().then(setIdentity).catch(() => {}); load() }, [])
  const total = useMemo(() => allocations.reduce((sum, item) => sum + Number(item.pourcentage || 0), 0), [allocations])
  const directAllocations = useMemo(() => allocations.filter((item) => !['fonctionnement_general', 'fonctionnement_interne'].includes(item.code)), [allocations])
  const generalAllocation = useMemo(() => allocations.find((item) => item.code === 'fonctionnement_general'), [allocations])
  const internalAllocation = useMemo(() => allocations.find((item) => item.code === 'fonctionnement_interne'), [allocations])
  const functioningTotal = Number(generalAllocation?.pourcentage || 0) + Number(internalAllocation?.pourcentage || 0)

  function changeType(code) {
    const parameter = settings.parametres?.find((item) => item.type_frais === code && item.est_actif)
    const type = settings.types_frais.find((item) => item.code === code)
    setSelectedType(code); setAllocations(parameter?.allocations || defaultAllocations(settings.categories)); setParameterName(parameter?.nom || `Repartition frais ${type?.libelle || ''}`); setAcceptsDime(parameter?.accepte_dime || false); setDimePercent(String(parameter?.pourcentage_dime ?? 10)); setNotice(''); setError('')
  }
  function changePercent(categoryId, value) {
    setAllocations((items) => items.map((item) => item.categorie_id === categoryId ? { ...item, pourcentage: value } : item))
  }
  function changeFunctioningTotal(value) {
    const nextTotal = Math.min(Math.max(Number(value || 0), 0), 100)
    const nextInternal = Math.min(Number(internalAllocation?.pourcentage || 0), nextTotal)
    setAllocations((items) => items.map((item) => {
      if (item.code === 'fonctionnement_interne') return { ...item, pourcentage: nextInternal }
      if (item.code === 'fonctionnement_general') return { ...item, pourcentage: nextTotal - nextInternal }
      return item
    }))
  }
  function changeFunctioningShare(code, value) {
    const share = Math.min(Math.max(Number(value || 0), 0), functioningTotal)
    setAllocations((items) => items.map((item) => {
      if (item.code === code) return { ...item, pourcentage: share }
      if (item.code === 'fonctionnement_general') return { ...item, pourcentage: functioningTotal - share }
      if (item.code === 'fonctionnement_interne') return { ...item, pourcentage: functioningTotal - share }
      return item
    }))
  }
  async function saveSettings() {
    setNotice(''); setError('')
    if (Math.round(total * 100) !== 10000) { setError('Le total doit etre exactement egal a 100 %.'); return false }
    if (acceptsDime && (Number(dimePercent) < 0 || Number(dimePercent) > 100 || Number.isNaN(Number(dimePercent)))) { setError('Le pourcentage de dime doit etre compris entre 0 et 100 %.'); return false }
    setSaving(true)
    try {
      if (!parameterName.trim()) { setError('Donnez un nom au parametre.'); return false }
      const result = await saveRepartitionSettings({ nom: parameterName.trim(), type_frais: selectedType, accepte_dime: acceptsDime, pourcentage_dime: dimePercent, allocations: allocations.map((item) => ({ categorie_id: item.categorie_id, pourcentage: item.pourcentage })) })
      setNotice(`${result.paiements_repartis || 0} paiement(s) de l'annee scolaire active ont ete repartis.`)
      await load()
      return true
    } catch (requestError) { setError(requestError.message || 'Enregistrement impossible.'); return false } finally { setSaving(false) }
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
    setSelectedType(type.code); setParameterName(`Repartition frais ${type.libelle}`); setAcceptsDime(false); setDimePercent('10'); setAllocations(defaultAllocations(settings.categories)); setIsCreateModalOpen(true)
  }
  function selectParameter(parameter) { setSelectedType(parameter.type_frais); setParameterName(parameter.nom); setAcceptsDime(parameter.accepte_dime); setDimePercent(String(parameter.pourcentage_dime ?? 10)); setAllocations(parameter.allocations); setIsCreateModalOpen(true) }
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
        {!isSettings && <button className="dime-summary-button" type="button" onClick={() => setIsDimeModalOpen(true)}>
          <span>Consultation confidentielle</span>
          <b>Voir la dîme retirée</b>
          <small>Le montant n’apparaît pas dans le tableau des répartitions.</small>
        </button>}
        <section className="repartition-kpis">
          <article><span>Montant reparti</span><strong>{money(dashboard.total)}</strong><small>apres deduction eventuelle de la dime</small></article>
          <article><span>Repartition du jour</span><strong>{money(dashboard.today_total)}</strong><small>paiements du jour</small></article>
          <article><span>Paiements ventiles</span><strong>{dashboard.payment_count}</strong><small>avec detail disponible</small></article>
        </section>
        <section className="repartition-grid">
          <article className="repartition-card settings-card">
            <div className="repartition-card-head"><div><span>Parametres</span><h2>Cle de repartition</h2></div><button className="parameter-add" type="button" onClick={openNewParameter}>+ Ajouter</button></div>
            <div className="parameter-list">{settings.parametres?.map((parameter) => <button type="button" key={parameter.id} onClick={() => selectParameter(parameter)}><span><b>{parameter.nom}</b><small>{parameter.type_frais_libelle}</small></span><em className={parameter.est_actif ? 'parameter-active' : ''}>{parameter.est_actif ? 'Actif' : 'Archive'}</em></button>)}</div>
            {isCreateModalOpen && <div className="parameter-modal-backdrop"><div className="parameter-modal"><div className="repartition-card-head"><div><span>Nouveau parametre</span><h2>Cle de repartition</h2></div><button className="modal-close" type="button" onClick={() => setIsCreateModalOpen(false)}>×</button></div><label className="repartition-select">Nom du parametre<input value={parameterName} placeholder="Ex. Repartition frais d'inscription 2026" onChange={(event) => setParameterName(event.target.value)} /></label>
            <label className="repartition-select">Type de frais<select value={selectedType} onChange={(event) => changeType(event.target.value)}>{settings.types_frais.map((type) => <option key={type.code} value={type.code}>{type.libelle}</option>)}</select></label>
            <label className="dime-choice"><input type="checkbox" checked={acceptsDime} onChange={(event) => setAcceptsDime(event.target.checked)} /><span><b>Ce paramètre accepte la dîme</b><small>La dîme est retirée avant de répartir le solde entre les quatre rubriques.</small></span></label>
            {acceptsDime && <label className="repartition-select">Pourcentage de dime<input type="number" min="0" max="100" step="0.01" value={dimePercent} onChange={(event) => setDimePercent(event.target.value)} /></label>}
            <div className="allocation-list">{allocations.length ? <>{directAllocations.map((item) => <div className="allocation-row" key={item.categorie_id}><i style={{ background: item.couleur }} /><label>{item.libelle}<input aria-label={`Pourcentage ${item.libelle}`} type="number" min="0" max="100" step="0.01" value={item.pourcentage} onChange={(event) => changePercent(item.categorie_id, event.target.value)} /></label><b>%</b></div>)}{generalAllocation && internalAllocation && <section className="functioning-allocation"><header><div><b>Fonctionnement</b><small>Définissez d’abord son pourcentage total, puis répartissez-le entre les deux tranches.</small></div><label>Total fonctionnement<input aria-label="Pourcentage total fonctionnement" type="number" min="0" max="100" step="0.01" value={functioningTotal} onChange={(event) => changeFunctioningTotal(event.target.value)} /><b>%</b></label></header><div className="functioning-splits"><label><span>Fonctionnement général</span><input aria-label="Pourcentage fonctionnement général" type="number" min="0" max={functioningTotal} step="0.01" value={generalAllocation.pourcentage} onChange={(event) => changeFunctioningShare('fonctionnement_general', event.target.value)} /><b>%</b></label><label><span>Fonctionnement interne</span><input aria-label="Pourcentage fonctionnement interne" type="number" min="0" max={functioningTotal} step="0.01" value={internalAllocation.pourcentage} onChange={(event) => changeFunctioningShare('fonctionnement_interne', event.target.value)} /><b>%</b></label></div></section>}</> : <p className="settings-help">Aucune categorie de repartition active. Ajoutez d'abord les categories dans l'administration pour definir leurs pourcentages.</p>}</div>
            <p className="settings-help">A l'enregistrement, la cle est appliquee a tous les paiements deja enregistres pour ce type de frais dans l'annee scolaire active, puis aux nouveaux encaissements.</p>
            <button className="save-repartition" type="button" disabled={saving || !allocations.length} onClick={async () => { if (await saveSettings()) { setIsCreateModalOpen(false); window.location.hash = 'repartition' } }}>{saving ? 'Enregistrement...' : 'Enregistrer et voir la repartition'}</button></div></div>}
          </article>
          <article className="repartition-card summary-card"><div className="repartition-card-head"><div><span>Vue consolidee</span><h2>Repartition encaissee</h2></div></div>
            <div className="category-summary">{dashboard.by_category.map((item) => <article className="category-cell" key={item.id} style={{ '--category-color': item.couleur }}><div className="category-cell-top"><i /><span>{item.libelle}</span></div><strong>{money(item.amount)}</strong><div className="progress"><em style={{ width: `${item.percent}%` }} /></div><small>{item.percent} % du total reparti</small></article>)}</div>
          </article>
        </section>
        <section className="repartition-card payments-card"><div className="repartition-card-head"><div><span>Traçabilite</span><h2>Details par paiement</h2></div><small>Cliquez sur une ligne pour consulter sa ventilation.</small></div>
          <div className="payment-table"><div className="payment-row table-head"><span>Recu / date</span><span>Eleve et frais</span><span>Encaisse</span><span /></div>{dashboard.payments.length === 0 ? <p className="fees-empty">Aucun paiement reparti pour le moment.</p> : dashboard.payments.map((payment) => <button className="payment-row" key={payment.id} type="button" onClick={() => setOpenPayment(openPayment?.id === payment.id ? null : payment)}><span><b>{payment.reference}</b><small>{payment.date}</small></span><span><b>{payment.eleve}</b><small>{payment.type_frais}</small></span><strong>{money(payment.amount)}</strong><span className="chevron">{openPayment?.id === payment.id ? '−' : '+'}</span>{openPayment?.id === payment.id && <div className="payment-detail">{payment.allocations.map((allocation) => <div key={allocation.libelle}><i style={{ background: allocation.couleur }} />{allocation.libelle}<small>{allocation.pourcentage} %</small><b>{money(allocation.montant)}</b></div>)}</div>}</button>)}</div>
        </section>
        {isDimeModalOpen && <div className="parameter-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setIsDimeModalOpen(false) }}><section className="parameter-modal dime-modal" role="dialog" aria-modal="true" aria-labelledby="dime-modal-title"><div className="repartition-card-head"><div><span>Montant retiré avant répartition</span><h2 id="dime-modal-title">Dîme</h2></div><button className="modal-close" type="button" aria-label="Fermer" onClick={() => setIsDimeModalOpen(false)}>×</button></div><div className="dime-modal-amount"><span>Dîme prélevée pour la période sélectionnée</span><strong>{money(dashboard.dime_total)}</strong><small>Ce montant est déduit des encaissements concernés avant le calcul des parts du propriétaire, des enseignants et du fonctionnement.</small></div><button className="save-repartition" type="button" onClick={() => setIsDimeModalOpen(false)}>Fermer</button></section></div>}
      </>}
    </section>
  </main>
}

export default RepartitionPage
