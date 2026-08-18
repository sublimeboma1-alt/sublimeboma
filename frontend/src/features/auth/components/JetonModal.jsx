import { useState, useEffect, useRef } from 'react'
import { useJeton } from '../context/JetonContext'

function JetonModal({ isOpen, onClose, onSuccess }) {
  const { valider, isVerifying, erreur, setErreur } = useJeton()
  const [code, setCode] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    if (isOpen) {
      setCode('')
      setErreur('')
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen, setErreur])

  async function handleSubmit(event) {
    event.preventDefault()
    if (!code.trim()) return
    const resultat = await valider(code.trim())
    if (resultat.success) {
      onSuccess?.(resultat.perimetre)
      onClose?.()
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal-panel jeton-modal" role="dialog" aria-modal="true" aria-labelledby="jeton-title">
        <header className="modal-header">
          <div>
            <p>Acces finance</p>
            <h2 id="jeton-title">Code Jeton requis</h2>
          </div>
          <button type="button" className="icon-action" onClick={onClose} aria-label="Fermer">X</button>
        </header>

        <form className="student-form" onSubmit={handleSubmit}>
          <div className="jeton-info">
            <p>Saisissez le code jeton pour acceder aux fonctionnalites financieres.</p>
            <small>Le code est cree par l'administrateur et donne acces aux donnees specifiques liees au jeton.</small>
          </div>

          <label>
            Code jeton
            <input
              ref={inputRef}
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Ex: A1B2C3D4E5F6G7H8"
              maxLength={64}
              autoComplete="off"
              disabled={isVerifying}
              className="jeton-input"
            />
          </label>

          {erreur && <div className="form-error">{erreur}</div>}

          <div className="modal-actions">
            <button type="button" className="ghost-action" onClick={onClose} disabled={isVerifying}>
              Annuler
            </button>
            <button type="submit" className="primary-action" disabled={isVerifying || !code.trim()}>
              {isVerifying ? 'Verification...' : 'Valider'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

export default JetonModal