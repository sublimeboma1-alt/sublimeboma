import { useEffect, useState } from 'react'
import AppNavbar from '../../../components/AppNavbar'
import { defaultIdentity, fetchIdentity } from '../../../services/identityService'
import { useAuth } from '../../auth/context/authState'
import { createPayment, fetchEleveDetail, fetchFeesReferences } from '../services/fraisService'
import PaymentModal from '../components/PaymentModal'

const formatMoney = (amount) => new Intl.NumberFormat('fr-FR').format(amount) + ' FC'

function statusBadge(statut) {
  if (statut === 'paid' || statut === 'paye') return ['Paye', 'paid']
  if (statut === 'late' || statut === 'non_paye') return ['Impaye', 'late']
  return ['Partiel', 'partial']
}

function EleveFraisDetailPage({ eleveId, onBack }) {
  const { user, signOut } = useAuth()
  const [identity, setIdentity] = useState(defaultIdentity)
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState('')
  const [references, setReferences] = useState({ modes_paiement: [] })
  const [paymentTarget, setPaymentTarget] = useState(null)

  useEffect(() => {
    fetchIdentity().then(setIdentity).catch(() => {})
  }, [])

  useEffect(() => {
    let mounted = true
    fetchFeesReferences().then((refs) => { if (mounted) setReferences(refs) }).catch(() => {})
    fetchEleveDetail(eleveId)
      .then((data) => { if (mounted) setDetail(data) })
      .catch((err) => { if (mounted) setError(err.message || 'Impossible de charger le detail.') })
    return () => { mounted = false }
  }, [eleveId])

  function navigate(action) {
    if (action === 'eleves.list') window.location.hash = 'eleves'
    if (action === 'fees.dashboard') { window.location.hash = 'frais' }
    if (action === 'fees.statistics') { window.location.hash = 'statistiques' }
    if (action === 'fees.situation') { window.location.hash = 'frais-situation' }
    if (action === 'fees.years') { window.location.hash = 'frais-annees' }
    if (action === 'fees.tariffs') { window.location.hash = 'frais-tarifs' }
    if (action === 'fees.apply') { window.location.hash = 'frais-appliquer' }
    if (action === 'finances.depenses') { window.location.hash = 'depenses' }
    if (action === 'session.logout') signOut()
  }

  function openPayment(trimestre) {
    const payableFees = trimestre.frais.filter((frais) => frais.balance > 0)
    const defaultFee = payableFees.find((frais) => frais.type_frais.trim().toLowerCase() === 'minerval') || payableFees[0]
    if (defaultFee) setPaymentTarget({ trimestre, frais: defaultFee, fraisOptions: payableFees })
  }

  async function handlePayment({ fraisId, amount: value, modeCode, description }) {
    await createPayment({ frais_id: fraisId, montant_paye: value, mode_paiement: modeCode, description })
    const data = await fetchEleveDetail(eleveId)
    setDetail(data)
    setPaymentTarget(null)
  }

  const paymentHistory = (detail?.trimestres || [])
    .flatMap((trimestre) => trimestre.frais.flatMap((frais) => (frais.paiements || []).map((payment) => ({ ...payment, trimestre: trimestre.trimestre, typeFrais: frais.type_frais }))))
    .sort((first, second) => `${second.date}-${second.id}`.localeCompare(`${first.date}-${first.id}`))

  return (
    <main className="app-shell fees-shell">
      <AppNavbar identity={identity} onNavigate={navigate} />
      <section className="workspace fees-workspace">
        <header className="fees-header">
          <div>
            <p>Gestion financiere · {detail ? detail.annee_scolaire : 'Annee scolaire'}</p>
            <h1>Situation de l eleve</h1>
            <span>Consultez les frais, paiements et soldes de l eleve.</span>
          </div>
          <div className="fees-header-actions">
            <span className="user-chip">{user?.username}</span>
          </div>
        </header>

        <button type="button" className="fees-back-btn" onClick={onBack}>
          <span aria-hidden="true">←</span> Retour a la situation des eleves
        </button>

        {error && !detail ? (
          <div className="error-state">{error}</div>
        ) : detail && (
          <>
            <section className="fees-detail-card">
              <div className="fees-detail-head">
                <div className="dossier-avatar fees-detail-avatar">{detail.name.split(' ').map((part) => part[0]).join('')}</div>
                <div>
                  <h2>{detail.name}</h2>
                  <p className="fees-detail-meta">
                    {detail.matricule} · {detail.classe}{detail.option ? ` · ${detail.option}` : ''} · {detail.annee_scolaire}
                  </p>
                </div>
                <span className={`payment-status ${detail.statut === 'paid' ? 'paid' : detail.statut === 'late' ? 'late' : 'partial'}`}>
                  {statusBadge(detail.statut)[0]}
                </span>
              </div>
              <div className="fees-detail-sommaire">
                <div><span>A payer</span><strong>{formatMoney(detail.total)}</strong></div>
                <div><span>Paye</span><strong className="text-paid">{formatMoney(detail.paid)}</strong></div>
                <div><span>Solde</span><strong className="text-late">{formatMoney(detail.balance)}</strong></div>
                <div><span>Taux</span><strong>{detail.total ? Math.round((detail.paid / detail.total) * 100) : 0}%</strong></div>
              </div>
            </section>

            <div className="fees-detail-trimestres">
              {detail.trimestres.length === 0 && <p className="fees-empty">Aucun frais affecte.</p>}
              {detail.trimestres.map((trimestre) => {
                const progress = trimestre.total ? Math.round((trimestre.paid / trimestre.total) * 100) : 0
                return (
                <article className="fees-trimestre" key={trimestre.trimestre}>
                  <div className="fees-trimestre-head">
                    <div className="fees-trimestre-title">
                      <span className="fees-trimestre-index">T{trimestre.trimestre}</span>
                      <div><span>Periode scolaire</span><h3>{trimestre.trimestre}e trimestre</h3></div>
                    </div>
                    <div className="fees-trimestre-actions">
                      <span className={`payment-status ${trimestre.balance <= 0 ? 'paid' : trimestre.paid === 0 ? 'late' : 'partial'}`}>
                        {trimestre.balance <= 0 ? 'Paye' : trimestre.paid === 0 ? 'Impaye' : 'Partiel'}
                      </span>
                    </div>
                  </div>
                  {trimestre.frais.some((frais) => frais.balance > 0) && (
                    <button type="button" className="fees-primary fees-trimestre-pay" onClick={() => openPayment(trimestre)}>
                      Payer ce trimestre
                    </button>
                  )}
                  <div className="fees-trimestre-total">
                    <div><span>Regle</span><strong>{formatMoney(trimestre.paid)} <small>sur {formatMoney(trimestre.total)}</small></strong></div>
                    <b>{progress}%</b>
                    <div className="fees-mini-progress"><i style={{ width: `${progress}%` }} /></div>
                  </div>
                  {trimestre.frais.map((frais) => {
                    const [label, key] = statusBadge(frais.statut)
                    return (
                      <div className="fees-frais-row" key={frais.id}>
                        <div className="fees-frais-info">
                          <strong>{frais.type_frais}</strong>
                          <span>{formatMoney(frais.montant)} · Paye {formatMoney(frais.paid)} · Solde {formatMoney(frais.balance)}</span>
                          <span className={`payment-status ${key}`}>{label}</span>
                        </div>
                      </div>
                    )
                  })}
                </article>
                )
              })}
            </div>
            <section className="fees-global-history">
              <div className="fees-global-history-head"><div><span>Suivi des encaissements</span><h2>Historique des paiements</h2></div><small>{paymentHistory.length} paiement{paymentHistory.length > 1 ? 's' : ''}</small></div>
              {paymentHistory.length === 0 ? <p className="fees-empty">Aucun paiement enregistre.</p> : <div className="fees-global-payments">
                {paymentHistory.map((payment) => (
                  <article className="fees-global-payment" key={payment.id}>
                    <div><span className="fees-reference">{payment.reference}</span><small>Enregistre le {payment.date}</small></div>
                    <div><span>Trimestre</span><strong>{payment.trimestre}</strong></div>
                    <div><span>Type de frais</span><strong>{payment.typeFrais}</strong></div>
                    <div><span>Mode</span><strong className="payment-method">{payment.method}</strong></div>
                    <div><span>Agent</span><strong>{payment.agent || 'Non renseigne'}</strong></div>
                    <strong className="fees-payment-amount">{formatMoney(payment.amount)}</strong>
                  </article>
                ))}
              </div>}
            </section>
          </>
        )}
      </section>

      {paymentTarget && (
        <PaymentModal
          detail={detail}
          trimestre={paymentTarget.trimestre}
          frais={paymentTarget.frais}
          fraisOptions={paymentTarget.fraisOptions}
          modesPaiement={references.modes_paiement || []}
          onClose={() => setPaymentTarget(null)}
          onSave={handlePayment}
        />
      )}
    </main>
  )
}

export default EleveFraisDetailPage
