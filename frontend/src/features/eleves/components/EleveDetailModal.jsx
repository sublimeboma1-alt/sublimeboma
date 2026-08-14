import { API_BASE_URL } from '../../../services/apiClient'

function DetailItem({ label, value }) {
  return (
    <div className="detail-item">
      <span>{label}</span>
      <strong>{value || '-'}</strong>
    </div>
  )
}

function EleveDetailModal({ eleve, onClose }) {
  if (!eleve) {
    return null
  }

  const photoUrl = eleve.photo_url?.startsWith('http') ? eleve.photo_url : `${API_BASE_URL}${eleve.photo_url || ''}`

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal-panel" role="dialog" aria-modal="true" aria-labelledby="eleve-detail-title">
        <header className="modal-header">
          <div>
            <p>{eleve.matricule}</p>
            <h2 id="eleve-detail-title">{eleve.nom_complet || `${eleve.nom} ${eleve.post_nom} ${eleve.prenom}`}</h2>
          </div>
          <button type="button" className="icon-action" onClick={onClose} aria-label="Fermer">X</button>
        </header>

        <div className="detail-profile">
          <div className="detail-photo">
            {eleve.photo_url ? <img src={photoUrl} alt="Photo de l'eleve" /> : <span>Photo</span>}
          </div>
          <div>
            <span>{eleve.classe || 'Non assigne'}</span>
            <strong>{eleve.niveau || 'Niveau non precise'}</strong>
          </div>
        </div>

        <div className="detail-grid">
          <DetailItem label="Classe" value={eleve.classe || 'Non assigne'} />
          <DetailItem label="Niveau" value={eleve.niveau} />
          <DetailItem label="Annee scolaire" value={eleve.annee_scolaire} />
          <DetailItem label="Sexe" value={eleve.sexe_display || eleve.sexe} />
          <DetailItem label="Statut" value={eleve.statut_display || eleve.statut} />
          <DetailItem label="Date naissance" value={eleve.date_naissance} />
          <DetailItem label="Lieu naissance" value={eleve.lieu_de_naissance} />
          <DetailItem label="Telephone" value={eleve.telephone} />
          <DetailItem label="Email" value={eleve.email} />
          <DetailItem label="MASP" value={eleve.est_masp ? 'Oui' : 'Non'} />
          <DetailItem label="Date inscription" value={eleve.date_inscription} />
        </div>

        <footer className="modal-actions">
          <button type="button" className="primary-action" onClick={onClose}>Fermer</button>
        </footer>
      </section>
    </div>
  )
}

export default EleveDetailModal
