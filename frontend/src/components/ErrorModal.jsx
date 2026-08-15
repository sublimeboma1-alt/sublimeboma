function ErrorModal({ message, onClose }) {
  if (!message) {
    return null
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal-panel api-error-modal" role="alertdialog" aria-modal="true" aria-labelledby="api-error-title">
        <header className="modal-header">
          <div>
            <p>Action non enregistree</p>
            <h2 id="api-error-title">Une erreur est survenue</h2>
          </div>
          <button type="button" className="icon-action" onClick={onClose} aria-label="Fermer">X</button>
        </header>
        <p>{message}</p>
        <footer className="modal-actions">
          <button type="button" className="primary-action" onClick={onClose}>Compris</button>
        </footer>
      </section>
    </div>
  )
}

export default ErrorModal
