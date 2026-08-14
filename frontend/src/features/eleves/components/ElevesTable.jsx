function getStatusLabel(statut) {
  const labels = {
    actif: 'Actif',
    inactif: 'Inactif',
    suspendu: 'Suspendu',
    diplome: 'Diplome',
  }

  return labels[statut] || statut
}

function ElevesTable({ eleves, onDelete, onEdit, onViewDetails }) {
  return (
    <div className="table-shell">
      <div className="table-titlebar">
        <div>
          <strong>Registre des eleves</strong>
          <span>{eleves.length} dossier(s)</span>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Matricule</th>
            <th>Nom complet</th>
            <th>Classe</th>
            <th>Sexe</th>
            <th>Statut</th>
            <th>MASP</th>
            <th>Telephone</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {eleves.map((eleve) => (
            <tr key={eleve.id || eleve.matricule}>
              <td className="mono">{eleve.matricule}</td>
              <td>
                <strong>{`${eleve.nom} ${eleve.post_nom} ${eleve.prenom}`}</strong>
                <span>{eleve.annee_scolaire || eleve.date_inscription}</span>
              </td>
              <td>{eleve.classe || 'Non assigne'}</td>
              <td>{eleve.sexe}</td>
              <td>
                <span className={`status-pill status-${eleve.statut}`}>{getStatusLabel(eleve.statut)}</span>
              </td>
              <td>{eleve.est_masp ? 'Oui' : 'Non'}</td>
              <td>{eleve.telephone || '-'}</td>
              <td>
                <div className="row-actions">
                  <button type="button" className="table-action" onClick={() => onViewDetails(eleve)}>
                    Detail
                  </button>
                  <button type="button" className="table-action" onClick={() => onEdit(eleve)}>
                    Modifier
                  </button>
                  <button type="button" className="table-action danger-text" onClick={() => onDelete(eleve)}>
                    Supprimer
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {eleves.length === 0 && <div className="empty-state">Aucun eleve trouve</div>}
    </div>
  )
}

export default ElevesTable
