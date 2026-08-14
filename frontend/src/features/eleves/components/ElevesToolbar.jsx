function ElevesToolbar({ filters, classes, references, onFilterChange }) {
  const filteredClasses = filters.niveau
    ? classes.filter((classe) => classe.niveau_code === filters.niveau)
    : classes

  return (
    <div className="eleves-toolbar">
      <div className="search-field">
        <span aria-hidden="true">S</span>
        <input
          value={filters.search}
          onChange={(event) => onFilterChange('search', event.target.value)}
          placeholder="Rechercher un eleve"
          type="search"
        />
      </div>

      <select
        value={filters.annee_scolaire}
        onChange={(event) => onFilterChange('annee_scolaire', event.target.value)}
      >
        <option value="">Annee active</option>
        {(references.annees_scolaires || []).map((annee) => (
          <option key={annee.id} value={annee.id}>
            {annee.annee}{annee.est_active ? ' active' : ''}
          </option>
        ))}
        <option value="toutes">Toutes les annees</option>
      </select>

      <select value={filters.niveau} onChange={(event) => onFilterChange('niveau', event.target.value)}>
        <option value="">Tous les niveaux</option>
        {(references.niveaux || []).map((niveau) => (
          <option key={niveau.code} value={niveau.code}>
            {niveau.libelle}
          </option>
        ))}
      </select>

      <select value={filters.classe_id} onChange={(event) => onFilterChange('classe_id', event.target.value)}>
        <option value="">Toutes les classes</option>
        {filteredClasses.map((classe) => (
          <option key={classe.id} value={classe.id}>
            {classe.nom}
          </option>
        ))}
      </select>

      <select value={filters.statut} onChange={(event) => onFilterChange('statut', event.target.value)}>
        <option value="">Tous les statuts</option>
        {(references.statuts || []).map((statut) => (
          <option key={statut.code} value={statut.code}>
            {statut.libelle}
          </option>
        ))}
      </select>

      <select value={filters.sexe} onChange={(event) => onFilterChange('sexe', event.target.value)}>
        <option value="">Tous les sexes</option>
        {(references.sexes || []).map((sexe) => (
          <option key={sexe.code} value={sexe.code}>
            {sexe.libelle}
          </option>
        ))}
      </select>
    </div>
  )
}

export default ElevesToolbar
