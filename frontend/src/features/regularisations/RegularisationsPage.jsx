import { useCallback, useEffect, useState } from 'react'
import AppNavbar from '../../components/AppNavbar'
import { useAuth } from '../auth/context/authState'
import { apiClient } from '../../services/apiClient'

const BASE = '/regularisations/api'
const emptyData = { results: [], eleves: [], annees: [] }
const emptyForm = { eleve_id: '', annee_id: '', montant: '', reference: '', observations: '' }

export default function RegularisationsPage() {
  const { user, signOut } = useAuth()
  const [token, setToken] = useState('')
  const [tokenNotice, setTokenNotice] = useState('')
  const [active, setActive] = useState(false)
  const [data, setData] = useState(emptyData)
  const [form, setForm] = useState(emptyForm)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => setData(await apiClient.get(`${BASE}/declarations/`)), [])

  useEffect(() => {
    function activateToken(code) {
      if (!code) return
      setTokenNotice(code)
      setActive(true)
      setMessage('Jeton admin active pour cette session.')
    }
    const pendingCode = sessionStorage.getItem('regularisations_jeton_generated_code')
    if (pendingCode) {
      activateToken(pendingCode)
      sessionStorage.removeItem('regularisations_jeton_generated_code')
    }
    function onTokenCreated(event) { activateToken(event.detail) }
    window.addEventListener('regularisations:token-created', onTokenCreated)
    return () => window.removeEventListener('regularisations:token-created', onTokenCreated)
  }, [])
  useEffect(() => {
    if (active) load().catch((e) => setError(e.message))
  }, [active, load])

  async function openToken(event) {
    event.preventDefault(); setBusy(true); setError('')
    try { await apiClient.post(`${BASE}/jeton/ouvrir/`, { code: token }); setActive(true); setMessage('Jeton de regularisation actif.') }
    catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  async function closeToken() {
    await apiClient.post(`${BASE}/jeton/fermer/`, {})
    setActive(false); setToken(''); setTokenNotice(''); setData(emptyData)
  }

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('')
    try {
      await apiClient.post(`${BASE}/declarations/`, form)
      setMessage('Declaration en attente. Seule une validation admin la comptera pour l annee active.')
      setForm(emptyForm); await load()
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  async function decide(item, decision) {
    setBusy(true); setError('')
    try { await apiClient.post(`${BASE}/declarations/${item.id}/validation/`, { decision }); await load() }
    catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  return <>
    <AppNavbar onNavigate={(action) => action === 'session.logout' && signOut?.()} />
    <main style={{ maxWidth: 1100, margin: '32px auto', padding: 20 }}>
      <p style={{ color: '#0c756f', fontWeight: 800 }}>ADMINISTRATION · REGLEMENTS SCOLAIRES</p>
      <h1>Declarations de reglement par annee</h1>
      <p>Les declarations en attente ne comptent pas. Apres validation, seul un reglement de l annee active s ajoute au total paye et reduit le solde.</p>
      {error && <p role="alert" style={{ color: '#a2313a' }}>{error}</p>}
      {message && <p role="status" style={{ color: '#087164' }}>{message}</p>}
      {!active ? <>
        <form onSubmit={openToken} style={{ display: 'flex', gap: 10, margin: '24px 0' }}>
          <input aria-label="Jeton de regularisation" placeholder="Jeton de regularisation" value={token} onChange={(event) => setToken(event.target.value)} required />
          <button disabled={busy}>Ouvrir avec le jeton</button>
        </form>
      </> : <>
        <button type="button" onClick={closeToken}>Verrouiller le module</button>
        {tokenNotice && <p role="status" style={{ padding: 12, background: '#eefaf8' }}>Nouveau jeton a copier : <code>{tokenNotice}</code></p>}
        <form onSubmit={submit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 12, margin: '24px 0', padding: 18, background: '#f7fafb', borderRadius: 12 }}>
          <label>Eleve<select required value={form.eleve_id} onChange={(event) => setForm({ ...form, eleve_id: event.target.value })}><option value="">Choisir</option>{data.eleves.map((item) => <option key={item.id} value={item.id}>{item.nom}</option>)}</select></label>
          <label>Annee scolaire<select required value={form.annee_id} onChange={(event) => setForm({ ...form, annee_id: event.target.value })}><option value="">Choisir</option>{data.annees.map((item) => <option key={item.id} value={item.id}>{item.annee}{item.active ? ' (active)' : ''}</option>)}</select></label>
          <label>Montant declare<input required type="number" min="0.01" step="0.01" value={form.montant} onChange={(event) => setForm({ ...form, montant: event.target.value })} /></label>
          <label>Reference<input value={form.reference} onChange={(event) => setForm({ ...form, reference: event.target.value })} /></label>
          <label>Observations<input value={form.observations} onChange={(event) => setForm({ ...form, observations: event.target.value })} /></label>
          <button disabled={busy}>Enregistrer en attente</button>
        </form>
        <div style={{ overflowX: 'auto' }}><table style={{ width: '100%', borderCollapse: 'collapse' }}><thead><tr>{['Eleve', 'Annee', 'Montant', 'Date', 'Reference', 'Statut', 'Validation admin'].map((label) => <th key={label} style={{ textAlign: 'left', padding: 10 }}>{label}</th>)}</tr></thead><tbody>
          {data.results.map((item) => <tr key={item.id} style={{ borderTop: '1px solid #e3eaee' }}><td style={{ padding: 10 }}>{item.eleve}</td><td>{item.annee}</td><td>{item.montant}</td><td>{item.date}</td><td>{item.reference || '—'}</td><td>{item.statut}</td><td>{item.statut === 'en_attente' && user?.is_staff && <><button disabled={busy} onClick={() => decide(item, 'valide')}>Valider</button> <button disabled={busy} onClick={() => decide(item, 'refuse')}>Refuser</button></>}</td></tr>)}
        </tbody></table></div>
      </>}
    </main>
  </>
}