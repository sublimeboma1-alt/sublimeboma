function ElevesStats({ eleves }) {
  const actifs = eleves.filter((eleve) => eleve.statut === 'actif').length
  const filles = eleves.filter((eleve) => eleve.sexe === 'F').length
  const masp = eleves.filter((eleve) => eleve.est_masp).length
  const classes = new Set(eleves.map((eleve) => eleve.classe).filter(Boolean)).size

  const stats = [
    { label: 'Eleves', value: eleves.length },
    { label: 'Actifs', value: actifs },
    { label: 'Filles', value: filles },
    { label: 'MASP', value: masp },
    { label: 'Classes', value: classes },
  ]

  return (
    <section className="stats-grid" aria-label="Statistiques eleves">
      {stats.map((stat) => (
        <article className="stat-card" key={stat.label}>
          <span>{stat.label}</span>
          <strong>{stat.value}</strong>
        </article>
      ))}
    </section>
  )
}

export default ElevesStats
