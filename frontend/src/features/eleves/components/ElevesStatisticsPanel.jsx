function countBy(items, getKey) {
  return items.reduce((accumulator, item) => {
    const key = getKey(item) || 'Non precise'
    accumulator[key] = (accumulator[key] || 0) + 1
    return accumulator
  }, {})
}

function toRows(counts) {
  return Object.entries(counts)
    .sort(([firstLabel], [secondLabel]) => firstLabel.localeCompare(secondLabel))
    .map(([label, total]) => ({ label, total }))
}

function SummaryTable({ title, rows, total, tone }) {
  return (
    <section className={`summary-panel summary-panel-${tone}`}>
      <div className="summary-titlebar">
        <div>
          <span className="summary-kicker">Repartition</span>
          <strong>{title}</strong>
        </div>
        <span className="summary-count">{rows.length} categorie(s)</span>
      </div>
      <div className="summary-rows">
        {rows.map((row) => {
          const percentage = total ? Math.round((row.total / total) * 100) : 0

          return (
            <div className="summary-row" key={row.label}>
              <div className="summary-row-label">
                <span>{row.label}</span>
                <strong>{row.total}</strong>
              </div>
              <div className="summary-track" aria-hidden="true">
                <span style={{ width: `${percentage}%` }} />
              </div>
              <small>{percentage}% de l'effectif</small>
            </div>
          )
        })}
      </div>
    </section>
  )
}

function MetricCard({ label, value, detail, tone }) {
  return (
    <article className={`statistics-metric metric-${tone}`}>
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
      <span className="metric-detail">{detail}</span>
    </article>
  )
}

function ElevesStatisticsPanel({ eleves, filters, onExport, isExporting }) {
  const total = eleves.length
  const actifs = eleves.filter((eleve) => eleve.statut === 'actif').length
  const filles = eleves.filter((eleve) => eleve.sexe === 'F').length
  const garcons = eleves.filter((eleve) => eleve.sexe === 'M').length
  const masp = eleves.filter((eleve) => eleve.est_masp).length
  const inactive = total - actifs
  const activeRate = total ? Math.round((actifs / total) * 100) : 0
  const classRows = toRows(countBy(eleves, (eleve) => eleve.classe || 'Non assigne'))
  const levelRows = toRows(countBy(eleves, (eleve) => eleve.niveau || 'Non precise'))
  const statusRows = toRows(countBy(eleves, (eleve) => eleve.statut_display || eleve.statut))
  const sexRows = toRows(countBy(eleves, (eleve) => eleve.sexe_display || eleve.sexe))
  const activeFilterCount = Object.values(filters).filter(Boolean).length

  return (
    <section className="statistics-view">
      <header className="statistics-head">
        <div className="statistics-heading">
          <p>Tableau de bord</p>
          <h2>Statistiques des eleves</h2>
          <span>Une lecture claire de l'effectif correspondant aux filtres actifs.</span>
        </div>
        <div className="statistics-head-actions">
          <span className="filter-badge">{activeFilterCount} filtre(s) actif(s)</span>
          <button type="button" className="statistics-export" onClick={onExport} disabled={isExporting}>
            <span aria-hidden="true">↓</span>
            {isExporting ? 'Export en cours...' : 'Exporter XLSX'}
          </button>
        </div>
      </header>

      <section className="statistics-overview" aria-label="Resume de l'effectif">
        <div className="overview-main">
          <span>Effectif analyse</span>
          <strong>{total}</strong>
          <p>eleve(s) dans le resultat actuel</p>
        </div>
        <div className="overview-rate">
          <span>Taux d'eleves actifs</span>
          <strong>{activeRate}%</strong>
          <div className="overview-progress" aria-label={`${activeRate}% d'eleves actifs`}>
            <span style={{ width: `${activeRate}%` }} />
          </div>
          <small>{actifs} actifs sur {total || 0} eleve(s)</small>
        </div>
      </section>

      <div className="statistics-metrics">
        <MetricCard label="Eleves actifs" value={actifs} detail={`${activeRate}% de l'effectif`} tone="green" />
        <MetricCard label="Autres statuts" value={inactive} detail="Inactifs, suspendus ou diplomes" tone="orange" />
        <MetricCard label="Filles" value={filles} detail={total ? `${Math.round((filles / total) * 100)}% de l'effectif` : 'Aucun resultat'} tone="purple" />
        <MetricCard label="Garcons" value={garcons} detail={total ? `${Math.round((garcons / total) * 100)}% de l'effectif` : 'Aucun resultat'} tone="blue" />
        <MetricCard label="Membres MASP" value={masp} detail={total ? `${Math.round((masp / total) * 100)}% de l'effectif` : 'Aucun resultat'} tone="gold" />
      </div>

      <div className="summary-grid">
        <SummaryTable title="Effectif par classe" rows={classRows} total={total} tone="teal" />
        <SummaryTable title="Effectif par niveau" rows={levelRows} total={total} tone="blue" />
        <SummaryTable title="Effectif par statut" rows={statusRows} total={total} tone="green" />
        <SummaryTable title="Effectif par sexe" rows={sexRows} total={total} tone="purple" />
      </div>
    </section>
  )
}

export default ElevesStatisticsPanel
