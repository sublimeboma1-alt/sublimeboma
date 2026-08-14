import { useState } from 'react'
import { API_BASE_URL } from '../../../services/apiClient'

const initialForm = {
  niveau_code: '',
  photo_file: null,
  nom: '',
  post_nom: '',
  prenom: '',
  lieu_de_naissance: '',
  date_naissance: '',
  sexe: 'M',
  adresse: '',
  telephone: '',
  email: '',
  est_masp: false,
  classe_id: '',
  statut: 'actif',
}

function getInitialForm(eleve) {
  if (!eleve) {
    return initialForm
  }

  return {
    niveau_code: eleve.niveau_code || '',
    photo_file: null,
    nom: eleve.nom || '',
    post_nom: eleve.post_nom || '',
    prenom: eleve.prenom || '',
    lieu_de_naissance: eleve.lieu_de_naissance || '',
    date_naissance: eleve.date_naissance || '',
    sexe: eleve.sexe || 'M',
    adresse: eleve.adresse || '',
    telephone: eleve.telephone || '',
    email: eleve.email || '',
    est_masp: Boolean(eleve.est_masp),
    classe_id: eleve.classe_id || '',
    statut: eleve.statut || 'actif',
  }
}

function getMediaUrl(url) {
  if (!url) {
    return ''
  }

  return url.startsWith('http') ? url : `${API_BASE_URL}${url}`
}

function EleveFormModal({ classes, eleve, references, isOpen, mode = 'create', onClose, onSubmit, isSaving }) {
  const [form, setForm] = useState(() => getInitialForm(eleve))
  const [photoPreview, setPhotoPreview] = useState(getMediaUrl(eleve?.photo_url))
  const selectedLevel = form.niveau_code
  const filteredClasses = selectedLevel
    ? classes.filter((classe) => classe.niveau_code === selectedLevel)
    : []
  const levelSummary = selectedLevel
    ? `${filteredClasses.length} classe${filteredClasses.length > 1 ? 's' : ''} disponible${filteredClasses.length > 1 ? 's' : ''}`
    : 'Choisir le niveau avant la classe'

  if (!isOpen) {
    return null
  }

  function handleChange(event) {
    const { checked, name, type, value } = event.target
    setForm((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
      ...(name === 'niveau_code' ? { classe_id: '' } : {}),
    }))
  }

  function handlePhotoChange(event) {
    const file = event.target.files?.[0] || null
    setForm((current) => ({ ...current, photo_file: file }))
    setPhotoPreview(file ? URL.createObjectURL(file) : getMediaUrl(eleve?.photo_url))
  }

  function handleSubmit(event) {
    event.preventDefault()
    const payload = { ...form }
    delete payload.niveau_code
    if (!payload.photo_file) {
      delete payload.photo_file
    }
    onSubmit(payload)
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal-panel modal-wide" role="dialog" aria-modal="true" aria-labelledby="eleve-form-title">
        <header className="modal-header">
          <div>
            <p>Nouveau dossier</p>
            <h2 id="eleve-form-title">{mode === 'edit' ? 'Modifier un eleve' : 'Ajouter un eleve'}</h2>
          </div>
          <button type="button" className="icon-action" onClick={onClose} aria-label="Fermer">X</button>
        </header>

        <form className="student-form" onSubmit={handleSubmit}>
          <div className="photo-field">
            <div className="photo-preview">
              {photoPreview ? <img src={photoPreview} alt="Photo de l'eleve" /> : <span>Photo</span>}
            </div>
            <label>
              Photo de l'eleve
              <input name="photo_file" type="file" accept="image/*" onChange={handlePhotoChange} />
              <span className="field-note">La photo sera optimisee automatiquement apres l'enregistrement.</span>
            </label>
          </div>

          <div className="form-grid">
            <label>
              Nom
              <input name="nom" value={form.nom} onChange={handleChange} required />
            </label>
            <label>
              Post-nom
              <input name="post_nom" value={form.post_nom} onChange={handleChange} required />
            </label>
            <label>
              Prenom
              <input name="prenom" value={form.prenom} onChange={handleChange} required />
            </label>
            <label>
              Lieu de naissance
              <input name="lieu_de_naissance" value={form.lieu_de_naissance} onChange={handleChange} />
            </label>
            <label>
              Date de naissance
              <input name="date_naissance" type="date" value={form.date_naissance} onChange={handleChange} />
            </label>
            <label>
              Sexe
              <select name="sexe" value={form.sexe} onChange={handleChange}>
                {(references.sexes || []).map((sexe) => (
                  <option key={sexe.code} value={sexe.code}>{sexe.libelle}</option>
                ))}
              </select>
            </label>
            <label>
              Niveau
              <select name="niveau_code" value={form.niveau_code} onChange={handleChange} required>
                <option value="">Selectionner un niveau</option>
                {(references.niveaux || []).map((niveau) => (
                  <option key={niveau.code} value={niveau.code}>{niveau.libelle}</option>
                ))}
              </select>
            </label>
            <label>
              Classe
              <select
                name="classe_id"
                value={form.classe_id}
                onChange={handleChange}
                disabled={!selectedLevel}
              >
                <option value="">{selectedLevel ? 'Non assigne' : 'Choisir le niveau'}</option>
                {filteredClasses.map((classe) => (
                  <option key={classe.id} value={classe.id}>{classe.nom}</option>
                ))}
              </select>
              <span className="field-note">{levelSummary}</span>
            </label>
            <label>
              Statut
              <select name="statut" value={form.statut} onChange={handleChange}>
                {(references.statuts || []).map((statut) => (
                  <option key={statut.code} value={statut.code}>{statut.libelle}</option>
                ))}
              </select>
            </label>
            <label>
              Telephone
              <input name="telephone" value={form.telephone} onChange={handleChange} />
            </label>
            <label>
              Email
              <input name="email" type="email" value={form.email} onChange={handleChange} />
            </label>
            <label className="check-field">
              <input name="est_masp" type="checkbox" checked={form.est_masp} onChange={handleChange} />
              Membre MASP
            </label>
          </div>

          <label>
            Adresse
            <textarea name="adresse" value={form.adresse} onChange={handleChange} rows="3" />
          </label>

          <footer className="modal-actions">
            <button type="button" className="ghost-action" onClick={onClose}>Annuler</button>
            <button type="submit" className="primary-action" disabled={isSaving}>
              {isSaving ? 'Enregistrement' : mode === 'edit' ? 'Mettre a jour' : 'Enregistrer'}
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}

export default EleveFormModal
