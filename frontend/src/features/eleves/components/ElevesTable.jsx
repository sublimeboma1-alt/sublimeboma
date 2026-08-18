import { API_BASE_URL } from '../../../services/apiClient'

function getStatusLabel(statut) {
  const labels = {
    actif: 'Actif',
    inactif: 'Inactif',
    suspendu: 'Suspendu',
    diplome: 'Diplome',
  }

  return labels[statut] || statut
}

function getInitials(eleve) {
  const parts = [eleve.nom, eleve.post_nom, eleve.prenom].filter(Boolean)
  if (parts.length === 0) return '?'
  return parts.slice(0, 2).map((p) => p.charAt(0).toUpperCase()).join('')
}

function getSexeLabel(sexe) {
  if (sexe === 'F') return 'Fille'
  if (sexe === 'M') return 'Garcon'
  return sexe || '-'
}

function ElevesTable({ eleves, onDelete, onEdit, onViewDetails }) {
  return (
    <div className="eleves-list-shell">
      <div className="eleves-list-header">
        <div>
          <strong>Registre des eleves</strong>
          <span>{eleves.length} dossier(s)</span>
        </div>
      </div>

      <div className="eleves-list-body">
        {eleves.map((eleve) => {
          const photoUrl = eleve.photo_url
            ? (eleve.photo_url.startsWith('http') ? eleve.photo_url : `${API_BASE_URL}${eleve.photo_url}`)
            : null

          return (
            <article
              key={eleve.id || eleve.matricule}
              className="eleve-card-row"
              onClick={() => onViewDetails(eleve)}
            >
              <div className="eleve-card-avatar">
                {photoUrl ? (
                  <img src={photoUrl} alt="Photo" />
                ) : (
                  <span>{getInitials(eleve)}</span>
                )}
              </div>

              <div className="eleve-card-main">
                <div className="eleve-card-name">
                  <strong>{`${eleve.nom} ${eleve.post_nom} ${eleve.prenom}`}</strong>
                  <span className="eleve-card-matricule">{eleve.matricule}</span>
                </div>
                <div className="eleve-card-meta">
                  <span className="eleve-meta-chip eleve-meta-classe">
                    {eleve.classe || 'Non assigne'}
                  </span>
                  <span className="eleve-meta-chip eleve-meta-sexe">
                    {getSexeLabel(eleve.sexe)}
                  </span>
                  {eleve.est_masp && (
                    <span className="eleve-meta-chip eleve-meta-masp">MASP</span>
                  )}
                  {eleve.telephone && (
                    <span className="eleve-meta-chip eleve-meta-phone">
                      {eleve.telephone}
                    </span>
                  )}
                </div>
              </div>

              <div className="eleve-card-side">
                <span className={`status-pill status-${eleve.statut}`}>
                  {getStatusLabel(eleve.statut)}
                </span>
              </div>

              <div className="eleve-card-actions" onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  className="eleve-action-btn eleve-action-view"
                  onClick={() => onViewDetails(eleve)}
                  title="Voir les details"
                >
                  Detail
                </button>
                <button
                  type="button"
                  className="eleve-action-btn eleve-action-edit"
                  onClick={() => onEdit(eleve)}
                  title="Modifier"
                >
                  Modifier
                </button>
                <button
                  type="button"
                  className="eleve-action-btn eleve-action-delete"
                  onClick={() => onDelete(eleve)}
                  title="Supprimer"
                >
                  Supprimer
                </button>
              </div>
            </article>
          )
        })}

        {eleves.length === 0 && (
          <div className="eleves-list-empty">
            <div className="eleves-empty-icon">?</div>
            <p>Aucun eleve trouve</p>
            <span>Modifiez vos filtres ou ajoutez un nouvel eleve</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default ElevesTable