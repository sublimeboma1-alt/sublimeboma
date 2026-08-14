import { useState } from 'react'

const formatMoney = (amount) => new Intl.NumberFormat('fr-FR').format(amount) + ' FC'

function PaymentModal({ detail, trimestre, frais, fraisOptions = [frais], modesPaiement, onClose, onSave }) {
  const defaultMode = modesPaiement.find((mode) => mode.code === 'cash') || modesPaiement[0]
  const [selectedFraisId, setSelectedFraisId] = useState(frais.id)
  const [amount, setAmount] = useState('')
  const [modeCode, setModeCode] = useState(defaultMode?.code || '')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const selectedFrais = fraisOptions.find((item) => item.id === Number(selectedFraisId)) || frais

  async function handleSubmit(event) {
    event.preventDefault()
    const value = Number(amount)
    if (!value || value <= 0) return
    setSaving(true)
    setError('')
    try {
      await onSave({ fraisId: selectedFrais.id, amount: value, modeCode, description })
    } catch (err) {
      setError(err.message || 'Impossible d enregistrer le paiement.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fees-modal-backdrop">
      <form className="fees-modal" onSubmit={handleSubmit}>
        <button type="button" className="fees-modal-close" onClick={onClose}>×</button>
        <span>Nouveau paiement</span>
        <h2>{detail.name}</h2>
        <p className="fees-payment-infos">
          {trimestre.trimestre}e trimestre · <strong>{selectedFrais.type_frais}</strong><br />
          Solde restant : <strong>{formatMoney(selectedFrais.balance)}</strong>
        </p>
        <label>Trimestre
          <select value={trimestre.trimestre} disabled><option>{trimestre.trimestre}e trimestre</option></select>
        </label>
        <label>Type de frais
          <select value={selectedFraisId} onChange={(event) => setSelectedFraisId(Number(event.target.value))}>
            {fraisOptions.map((item) => <option key={item.id} value={item.id}>{item.type_frais}</option>)}
          </select>
        </label>
        <label>Montant a encaisser
          <input autoFocus inputMode="numeric" value={amount} onChange={(event) => setAmount(event.target.value.replace(/\D/g, ''))} placeholder="Ex. 50000" required />
        </label>
        <label>Mode de paiement
          <select value={modeCode} onChange={(event) => setModeCode(event.target.value)}>
            {(modesPaiement.length ? modesPaiement : [{ code: 'cash', libelle: 'Especes' }]).map((mode) => <option key={mode.code} value={mode.code}>{mode.libelle}</option>)}
          </select>
        </label>
        <label>Observation (optionnel)
          <input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Ex. Paiement partiel" />
        </label>
        {error && <div className="error-state">{error}</div>}
        <div>
          <button type="button" onClick={onClose}>Annuler</button>
          <button type="submit" className="fees-primary" disabled={saving}>{saving ? 'Enregistrement...' : 'Valider le paiement'}</button>
        </div>
      </form>
    </div>
  )
}

export default PaymentModal
