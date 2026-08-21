import { useEffect, useMemo, useState } from 'react'
import AppNavbar from '../../../components/AppNavbar'
import { defaultIdentity, fetchIdentity } from '../../../services/identityService'
import { useAuth } from '../../auth/context/authState'
import { applyTariff, createPayment, createTariff, createYear, fetchFeesDashboard, fetchFeesReferences, fetchFeesStatistics, fetchPayments, fetchTariffs, fetchYears } from '../services/fraisService'

const formatMoney = (amount) => new Intl.NumberFormat('fr-FR').format(amount) + ' FC'

function statusFor(dossier) {
  if (dossier.paid >= dossier.total) return ['Paye', 'paid']
  if (dossier.paid === 0) return ['Impayé', 'late']
  return ['Partiel', 'partial']
}

function FraisScolairesPage({ initialTab }) {
  const { user, signOut } = useAuth()
  const [identity, setIdentity] = useState(defaultIdentity)
  const [tab, setTab] = useState(initialTab)
  const [dossiers, setDossiers] = useState([])
  const [payments, setPayments] = useState([])
  const [paymentsLoaded, setPaymentsLoaded] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [years, setYears] = useState([])
  const [tariffs, setTariffs] = useState([])
  const [references, setReferences] = useState({})
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')
  const [niveau, setNiveau] = useState('')
  const [classeFilter, setClasseFilter] = useState('')
  const [selected, setSelected] = useState(null)
  const [configModal, setConfigModal] = useState('')
  const [amount, setAmount] = useState('')
  const [applyTarget, setApplyTarget] = useState(null)
  const [statistics, setStatistics] = useState(null)
  const [statisticsFilters, setStatisticsFilters] = useState({ annee_scolaire: '', niveau: '', classe_id: '', type_frais: '', trimestre: '', date_debut: '', date_fin: '' })

  useEffect(() => { setTab(initialTab) }, [initialTab])
  useEffect(() => { fetchIdentity().then(setIdentity).catch(() => {}) }, [])
  useEffect(() => {
    let mounted = true
    Promise.all([fetchFeesDashboard(), fetchYears(), fetchTariffs(), fetchFeesReferences()])
      .then(([dashboard, yearRows, tariffRows, refs]) => {
        if (mounted) {
          setDossiers(dashboard.results || [])
          setYears(yearRows); setTariffs(tariffRows); setReferences(refs)
        }
      })
      .catch((error) => mounted && setLoadError(error.message || 'Impossible de charger les frais scolaires.'))
      .finally(() => mounted && setIsLoading(false))
    return () => { mounted = false }
  }, [])

  useEffect(() => {
    if (tab !== 'overview' || paymentsLoaded) return
    fetchPayments()
      .then((rows) => { setPayments(rows); setPaymentsLoaded(true) })
      .catch((error) => setLoadError(error.message || 'Impossible de charger les paiements.'))
  }, [tab, paymentsLoaded])

  useEffect(() => {
    if (tab !== 'statistics') return
    fetchFeesStatistics(statisticsFilters).then(setStatistics).catch((error) => setLoadError(error.message || 'Impossible de charger les statistiques.'))
  }, [tab, statisticsFilters])

  const totals = useMemo(() => dossiers.reduce((acc, item) => ({
    expected: acc.expected + item.total,
    paid: acc.paid + item.paid,
  }), { expected: 0, paid: 0 }), [dossiers])
  const recovery = totals.expected ? Math.round((totals.paid / totals.expected) * 100) : 0

  const filtered = dossiers.filter((item) => {
    const [label, key] = statusFor(item)
    const matchesQuery = `${item.name} ${item.matricule} ${item.classe}`.toLowerCase().includes(query.toLowerCase())
    const matchesStatus = status === 'all' || key === status
    const matchesNiveau = !niveau || item.niveau === niveau
    const matchesClasse = !classeFilter || item.classe === classeFilter
    return matchesQuery && matchesStatus && matchesNiveau && matchesClasse
  })

  function navigate(action) {
    if (action === 'eleves.list') window.location.hash = 'eleves'
    if (action === 'fees.dashboard') { setTab('overview'); window.location.hash = 'frais' }
    if (action === 'fees.statistics') { setTab('statistics'); window.location.hash = 'statistiques' }
    if (action === 'fees.situation') { setTab('dossiers'); window.location.hash = 'frais-situation' }
    if (action === 'fees.years') { setTab('years'); window.location.hash = 'frais-annees' }
    if (action === 'fees.tariffs') { setTab('tariffs'); window.location.hash = 'frais-tarifs' }
    if (action === 'fees.apply') { setTab('apply'); window.location.hash = 'frais-appliquer' }
    if (action === 'finances.repartition') { window.location.hash = 'repartition' }
    if (action === 'exports.open') { window.location.hash = 'exports' }
    if (action === 'finances.depenses') { window.location.hash = 'depenses' }
    if (action === 'session.logout') signOut()
  }

  async function reloadData() {
    try {
      const [dashboard, paymentRows, tariffRows] = await Promise.all([fetchFeesDashboard(), fetchPayments(), fetchTariffs()])
      setDossiers(dashboard.results || [])
      setPayments(paymentRows)
      setPaymentsLoaded(true)
      setTariffs(tariffRows)
    } catch (error) {
      setLoadError(error.message || 'Impossible de rafraichir les donnees.')
    }
  }

  async function recordPayment(event) {
    event.preventDefault()
    const paidAmount = Number(amount)
    if (!selected || !paidAmount || paidAmount <= 0) return
    try {
      await createPayment({ frais_id: selected.frais_id, montant_paye: paidAmount })
      await reloadData()
      setSelected(null)
      setAmount('')
    } catch (error) {
      setLoadError(error.message || 'Impossible d enregistrer le paiement.')
    }
  }

  const classesOptions = useMemo(() => {
    const classes = references.classes || []
    const unique = new Map()
    for (const c of classes) {
      if (!unique.has(c.libelle)) unique.set(c.libelle, c)
    }
    return [...unique.values()]
  }, [references])

  return (
    <main className="app-shell fees-shell">
      <AppNavbar identity={identity} onNavigate={navigate} />
      <section className="workspace fees-workspace">
        <header className="fees-header">
          <div>
            <p>Gestion financiere · Annee scolaire 2026-2027</p>
            <h1>Frais scolaires</h1>
            <span>Suivez les encaissements, les soldes et les dossiers de vos eleves.</span>
          </div>
          <div className="fees-header-actions">
            <span className="user-chip">{user?.username}</span>
          </div>
        </header>

        <nav className="fees-tabs" aria-label="Navigation des frais scolaires">
          {[['overview', 'Vue d’ensemble'], ['dossiers', 'Situation eleves'], ['years', 'Annees scolaires'], ['tariffs', 'Tarifs'], ['apply', 'Appliquer'], ['statistics', 'Statistiques']].map(([key, label]) => (
            <button key={key} type="button" className={tab === key ? 'active' : ''} onClick={() => setTab(key)}>{label}</button>
          ))}
        </nav>

        {loadError && <div className="error-state">{loadError}</div>}
        {isLoading ? <div className="loading-state">Chargement des frais scolaires...</div> : tab === 'overview' && <>
          <section className="fees-hero">
            <div><span>Montant encaisse</span><strong>{formatMoney(totals.paid)}</strong><small>sur {formatMoney(totals.expected)} attendus</small></div>
            <div className="fees-recovery"><span>Taux de recouvrement</span><strong>{recovery}%</strong><div><i style={{ width: `${recovery}%` }} /></div><small>{formatMoney(totals.expected - totals.paid)} restent a encaisser</small></div>
          </section>
          <section className="fees-kpis">
            <article><span>Dossiers regles</span><strong>{dossiers.filter((item) => item.paid >= item.total).length}</strong><small>paiement complet</small></article>
            <article><span>Paiements partiels</span><strong>{dossiers.filter((item) => item.paid > 0 && item.paid < item.total).length}</strong><small>a relancer</small></article>
            <article><span>Impayes</span><strong>{dossiers.filter((item) => item.paid === 0).length}</strong><small>action prioritaire</small></article>
            <article><span>Eleves MASP</span><strong>{dossiers.filter((item) => item.masp).length}</strong><small>dans la selection</small></article>
          </section>
          <section className="fees-panel"><div className="fees-panel-head"><div><span>Activite recente</span><h2>Derniers paiements enregistres</h2></div><button type="button" onClick={() => setTab('statistics')}>Voir les statistiques</button></div><PaymentsTable payments={payments.slice(0, 4)} /></section>
        </>}

        {!isLoading && tab === 'dossiers' && <section className="fees-panel">
          <div className="fees-panel-head">
            <div><span>Suivi individuel</span><h2>Dossiers des eleves</h2></div>
            <div className="fees-filters">
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Rechercher un eleve..." />
              <select value={niveau} onChange={(event) => { setNiveau(event.target.value); setClasseFilter('') }}>
                <option value="">Tous les niveaux</option>
                {(references.niveaux || []).map((x) => <option key={x.code} value={x.code}>{x.libelle}</option>)}
              </select>
              <select value={classeFilter} onChange={(event) => setClasseFilter(event.target.value)}>
                <option value="">Toutes les classes</option>
                {classesOptions.map((x) => <option key={x.id} value={x.libelle}>{x.libelle}</option>)}
              </select>
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="all">Tous les statuts</option>
                <option value="paid">Payes</option>
                <option value="partial">Partiels</option>
                <option value="late">Impayes</option>
              </select>
            </div>
          </div>
          <div className="fees-dossiers">
            {filtered.map((item) => {
              const [label, key] = statusFor(item)
              const rate = item.total ? Math.round((item.paid / item.total) * 100) : 0
              return (
                <article key={item.id} className="fees-dossier">
                  <div className="dossier-avatar">{item.name.split(' ').map((part) => part[0]).join('')}</div>
                  <div className="dossier-main">
                    <strong>{item.name}</strong>
                    <span>{item.matricule} · {item.classe}{item.option ? ` · ${item.option}` : ''}</span>
                  </div>
                  <div className="dossier-financials">
                    <div><span>A payer</span><strong>{formatMoney(item.total)}</strong></div>
                    <div><span>Paye</span><strong className="text-paid">{formatMoney(item.paid)}</strong></div>
                    <div><span>Solde</span><strong className="text-late">{formatMoney(item.total - item.paid)}</strong></div>
                    <div className="dossier-rate"><span>Taux</span><strong>{rate}%</strong><i style={{ width: `${rate}%` }} /></div>
                  </div>
                  <span className={`payment-status ${key}`}>{label}</span>
                  <div className="fees-dossier-action">
                    <button type="button" className="fees-btn-detail" onClick={() => { window.location.hash = `frais-situation/${item.id}` }}>Detail</button>
                  </div>
                </article>
              )
            })}
            {filtered.length === 0 && <p className="fees-empty">Aucun eleve trouve.</p>}
          </div>
        </section>}

        {!isLoading && tab === 'statistics' && <StatisticsPanel statistics={statistics} filters={statisticsFilters} setFilters={setStatisticsFilters} references={references} />}
        {!isLoading && tab === 'years' && <YearManager years={years} onOpen={() => setConfigModal('year')} />}
        {!isLoading && tab === 'tariffs' && <TariffManager references={references} tariffs={tariffs} onOpen={() => setConfigModal('tariff')} />}
        {!isLoading && tab === 'apply' && <ApplyTariff tariffs={tariffs} onSelect={setApplyTarget} />}
      </section>

      {selected && <div className="fees-modal-backdrop" role="presentation"><form className="fees-modal" onSubmit={recordPayment}><button type="button" className="fees-modal-close" onClick={() => setSelected(null)}>×</button><span>Nouveau paiement</span><h2>{selected.name}</h2><p>Solde restant : <strong>{formatMoney(selected.total - selected.paid)}</strong></p><label>Montant a encaisser<input autoFocus inputMode="numeric" value={amount} onChange={(event) => setAmount(event.target.value.replace(/\D/g, ''))} placeholder="Ex. 50000" /></label><div><button type="button" onClick={() => setSelected(null)}>Annuler</button><button type="submit" className="fees-primary">Valider le paiement</button></div></form></div>}
      {configModal === 'year' && <YearModal onClose={() => setConfigModal('')} onSave={async (data) => { const item = await createYear(data); setYears((rows) => [item, ...rows]); setConfigModal('') }} />}
      {configModal === 'tariff' && <TariffModalWithFeedback references={references} onClose={() => setConfigModal('')} onSave={async (data) => { await createTariff(data); setTariffs(await fetchTariffs()); setConfigModal('') }} />}
      {applyTarget && <ApplyModal tariff={applyTarget} onClose={() => setApplyTarget(null)} onConfirm={async () => { const result = await applyTariff(applyTarget.id); setApplyTarget(null); alert(`${result.created} frais crees pour ${result.eligible} eleves.`); await reloadData() }} />}
    </main>
  )
}

function PaymentsTable({ payments }) {
  return <div className="fees-table-wrap"><table className="fees-table"><thead><tr><th>Reference</th><th>Eleve</th><th>Montant</th><th>Mode</th><th>Date</th></tr></thead><tbody>{payments.map((payment) => <tr key={payment.id}><td className="fees-reference">{payment.reference}</td><td>{payment.name}</td><td><strong>{formatMoney(payment.amount)}</strong></td><td><span className="payment-method">{payment.method}</span></td><td>{payment.date}</td></tr>)}</tbody></table></div>
}

function StatisticsPanel({ statistics, filters, setFilters, references }) {
  const rows = statistics?.payments || []
  const classes = (references.classes || []).filter((item) => !filters.niveau || item.niveau === filters.niveau)
  const update = (key, value) => setFilters((current) => ({ ...current, [key]: value, ...(key === 'niveau' ? { classe_id: '' } : {}) }))
  const maxAmount = Math.max(...(statistics?.by_type || []).map((item) => item.amount), 1)
  if (!statistics) return <div className="loading-state">Chargement des statistiques...</div>
  return <section className="statistics-panel">
    <div className="fees-panel-head"><div><span>Analyse financiere</span><h2>Statistiques des frais</h2></div><small>Les paiements affiches respectent les filtres ci-dessous.</small></div>
    <div className="statistics-filters">
      <select value={filters.annee_scolaire} onChange={(e) => update('annee_scolaire', e.target.value)}><option value="">Annee active</option>{(references.annees_scolaires || []).map((item) => <option key={item.id} value={item.id}>{item.annee}</option>)}</select>
      <select value={filters.niveau} onChange={(e) => update('niveau', e.target.value)}><option value="">Tous les niveaux</option>{(references.niveaux || []).map((item) => <option key={item.code} value={item.code}>{item.libelle}</option>)}</select>
      <select value={filters.classe_id} onChange={(e) => update('classe_id', e.target.value)}><option value="">Toutes les classes</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.libelle}</option>)}</select>
      <select value={filters.type_frais} onChange={(e) => update('type_frais', e.target.value)}><option value="">Tous les types de frais</option>{(references.types_frais || []).map((item) => <option key={item.code} value={item.code}>{item.libelle}</option>)}</select>
      <select value={filters.trimestre} onChange={(e) => update('trimestre', e.target.value)}><option value="">Tous les trimestres</option>{[1, 2, 3].map((item) => <option key={item} value={item}>{item}e trimestre</option>)}</select>
      <label>Du<input type="date" value={filters.date_debut} onChange={(e) => update('date_debut', e.target.value)} /></label>
      <label>Au<input type="date" value={filters.date_fin} onChange={(e) => update('date_fin', e.target.value)} /></label>
    </div>
    <div className="statistics-kpis">
      <article><span>Montant attendu</span><strong>{formatMoney(statistics.expected)}</strong><small>Selon la selection</small></article>
      <article><span>Montant encaisse</span><strong>{formatMoney(statistics.collected)}</strong><small>{statistics.payment_count} paiement(s)</small></article>
      <article><span>Taux de recouvrement</span><strong>{statistics.recovery_rate}%</strong><small>Solde : {formatMoney(statistics.balance)}</small></article>
      <article><span>Aujourd'hui</span><strong>{statistics.today_count}</strong><small>{formatMoney(statistics.today_amount)} encaisse</small></article>
    </div>
    <div className="statistics-charts">
      <section><div className="statistics-section-head"><div><span>Repartition</span><h3>Par type de frais</h3></div></div>{statistics.by_type.length ? <div className="statistics-bars">{statistics.by_type.map((item) => <div key={item.label}><div><b>{item.label}</b><span>{formatMoney(item.amount)} · {item.percent}%</span></div><i><em style={{ width: `${Math.max((item.amount / maxAmount) * 100, 3)}%` }} /></i></div>)}</div> : <p className="statistics-empty">Aucun encaissement pour cette selection.</p>}</section>
      <section><div className="statistics-section-head"><div><span>Repartition</span><h3>Par trimestre</h3></div></div>{statistics.by_trimester.length ? <div className="statistics-rings">{statistics.by_trimester.map((item) => <div key={item.label}><b>{item.percent}%</b><span>{item.label}</span><small>{formatMoney(item.amount)}</small></div>)}</div> : <p className="statistics-empty">Aucun encaissement pour cette selection.</p>}</section>
    </div>
    <section className="fees-panel statistics-payments"><div className="fees-panel-head"><div><span>Details filtres</span><h2>Paiements enregistres</h2></div><small>{rows.length} resultat(s) affiche(s)</small></div><PaymentsTable payments={rows} /></section>
  </section>
}

function YearManager({ years, onOpen }) {
  return <section className="fees-panel"><div className="fees-panel-head"><div><span>Parametrage</span><h2>Annees scolaires</h2></div><button type="button" className="fees-primary" onClick={onOpen}>+ Nouvelle annee</button></div><div className="fees-dossiers">{years.map((year) => <article className="fees-dossier" key={year.id}><div className="dossier-avatar">AN</div><div className="dossier-main"><strong>{year.annee}</strong><span>{year.date_debut} au {year.date_fin}</span></div><span className={`payment-status ${year.est_active ? 'paid' : 'partial'}`}>{year.est_active ? 'Active' : 'Archivee'}</span></article>)}</div></section>
}

function TariffManager({ tariffs, onOpen }) {
  return <section className="fees-panel"><div className="fees-panel-head"><div><span>Definition des montants</span><h2>Configurer les tarifs</h2></div><button type="button" className="fees-primary" onClick={onOpen}>+ Nouveau tarif</button></div><PaymentsTable payments={tariffs.map((x) => ({ ...x, reference: x.trimestre, name: `${x.niveau} ${x.classe} ${x.option}`, amount: x.montant, method: x.type_frais, date: '' }))}/></section>
}

function YearModal({ onClose, onSave }) {
  const [form, setForm] = useState({ annee: '', date_debut: '', date_fin: '', est_active: false })
  return <div className="fees-modal-backdrop"><form className="fees-modal" onSubmit={async (e) => { e.preventDefault(); await onSave(form) }}><button type="button" className="fees-modal-close" onClick={onClose}>×</button><span>Parametrage</span><h2>Nouvelle annee scolaire</h2><label>Annee scolaire<input required placeholder="2026-2027" value={form.annee} onChange={(e) => setForm({ ...form, annee: e.target.value })}/></label><label>Date de debut<input required type="date" value={form.date_debut} onChange={(e) => setForm({ ...form, date_debut: e.target.value })}/></label><label>Date de fin<input required type="date" value={form.date_fin} onChange={(e) => setForm({ ...form, date_fin: e.target.value })}/></label><label><input type="checkbox" checked={form.est_active} onChange={(e) => setForm({ ...form, est_active: e.target.checked })}/> Rendre cette annee active</label><div><button type="button" onClick={onClose}>Annuler</button><button className="fees-primary">Enregistrer</button></div></form></div>
}

function TariffModal({ references, onClose, onSave }) {
  const [form, setForm] = useState({ classe_id: '', trimestre: '', type_frais: '', montant: '' })
  const [error, setError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const classes = useMemo(() => {
    const unique = new Map()
    for (const c of references.classes || []) {
      if (!unique.has(c.libelle)) unique.set(c.libelle, c)
    }
    return [...unique.values()]
  }, [references])

  return <div className="fees-modal-backdrop"><form className="fees-modal" onSubmit={async (e) => { e.preventDefault(); await onSave({ ...form, annee_scolaire_id: references.annee_active_id }) }}><button type="button" className="fees-modal-close" onClick={onClose}>×</button><span>Definition tarifaire</span><h2>Nouveau tarif</h2><label>Classe<select required className="fees-tariff-classe-select" value={form.classe_id} onChange={(e) => setForm({ ...form, classe_id: e.target.value })}><option value="">Choisir une classe</option>{classes.map((x) => <option key={x.id} value={x.id}>{x.libelle}</option>)}</select></label><label>Trimestre<select required value={form.trimestre} onChange={(e) => setForm({ ...form, trimestre: e.target.value })}><option value="">Choisir</option>{[1,2,3].map((x) => <option key={x} value={x}>{x}e trimestre</option>)}</select></label><label>Type de frais<select required value={form.type_frais} onChange={(e) => setForm({ ...form, type_frais: e.target.value })}><option value="">Choisir</option>{(references.types_frais || []).map((x) => <option key={x.code} value={x.code}>{x.libelle}</option>)}</select></label><label>Montant<input required inputMode="numeric" value={form.montant} onChange={(e) => setForm({ ...form, montant: e.target.value })}/></label><div><button type="button" onClick={onClose}>Annuler</button><button className="fees-primary" disabled={!references.annee_active_id}>Ajouter</button></div></form></div>
}

function ApplyTariff({ tariffs, onSelect }) { return <section className="fees-panel"><div className="fees-panel-head"><div><span>Distribution controlee</span><h2>Appliquer un tarif aux eleves</h2></div></div><div className="fees-dossiers">{tariffs.map((tariff) => <article className="fees-dossier" key={tariff.id}><div className="dossier-avatar">TF</div><div className="dossier-main"><strong>{tariff.type_frais} · {tariff.trimestre}</strong><span>{tariff.niveau} {tariff.classe} {tariff.option}</span></div><div className="dossier-progress"><span><b>{formatMoney(tariff.montant)}</b> par eleve</span></div><button type="button" onClick={() => onSelect(tariff)}>Appliquer</button></article>)}</div></section> }

function ApplyModal({ tariff, onClose, onConfirm }) {
  return <div className="fees-modal-backdrop"><div className="fees-modal"><button type="button" className="fees-modal-close" onClick={onClose}>×</button><span>Distribution controlee</span><h2>Appliquer ce tarif ?</h2><p><strong>{tariff.type_frais} · {tariff.trimestre}</strong></p><p>{tariff.niveau} {tariff.classe} {tariff.option}</p><p>Montant : <strong>{formatMoney(tariff.montant)}</strong> par eleve</p><div><button type="button" onClick={onClose}>Annuler</button><button className="fees-primary" onClick={onConfirm}>Confirmer</button></div></div></div>
}

function TariffModalWithFeedback({ references, onClose, onSave }) {
  const [form, setForm] = useState({ classe_id: '', trimestre: '', type_frais: '', montant: '' })
  const [error, setError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const classes = useMemo(() => {
    const unique = new Map()
    for (const item of references.classes || []) unique.set(item.id, item)
    return [...unique.values()]
  }, [references])

  async function submit(event) {
    event.preventDefault()
    setError('')
    setIsSaving(true)
    try {
      await onSave({ ...form, annee_scolaire_id: references.annee_active_id })
    } catch (saveError) {
      setError(saveError.message || 'Impossible de creer ce tarif.')
    } finally {
      setIsSaving(false)
    }
  }

  return <div className="fees-modal-backdrop"><form className="fees-modal" onSubmit={submit}>
    <button type="button" className="fees-modal-close" onClick={onClose}>×</button>
    <span>Definition tarifaire</span><h2>Nouveau tarif</h2>
    <label>Classe<select required className="fees-tariff-classe-select" value={form.classe_id} onChange={(event) => setForm({ ...form, classe_id: event.target.value })}><option value="">Choisir une classe</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.libelle}</option>)}</select></label>
    <label>Trimestre<select required value={form.trimestre} onChange={(event) => setForm({ ...form, trimestre: event.target.value })}><option value="">Choisir</option>{(references.trimestres || []).map((item) => <option key={item.code} value={item.code}>{item.libelle}</option>)}</select></label>
    <label>Type de frais<select required value={form.type_frais} onChange={(event) => setForm({ ...form, type_frais: event.target.value })}><option value="">Choisir</option>{(references.types_frais || []).map((item) => <option key={item.code} value={item.code}>{item.libelle}</option>)}</select></label>
    <label>Montant<input required inputMode="numeric" value={form.montant} onChange={(event) => setForm({ ...form, montant: event.target.value })}/></label>
    {error && <div className="form-error">{error}</div>}
    <div><button type="button" onClick={onClose} disabled={isSaving}>Annuler</button><button className="fees-primary" disabled={!references.annee_active_id || isSaving}>{isSaving ? 'Ajout...' : 'Ajouter'}</button></div>
  </form></div>
}

export default FraisScolairesPage
