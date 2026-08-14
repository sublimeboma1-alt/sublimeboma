import { useState } from 'react'
import { useAuth } from '../context/authState'

function LoginPage() {
  const { signIn, error, setError } = useAuth()
  const [form, setForm] = useState({ username: '', password: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  function handleChange(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)
    setError('')

    try {
      await signIn(form)
      window.location.hash = 'eleves'
    } catch (requestError) {
      setError(requestError.message || 'Connexion impossible.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="login-brand">
          <span>CS</span>
          <div>
            <p>Complexe Scolaire Sublime</p>
            <h1 id="login-title">Connexion</h1>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            Nom utilisateur
            <input
              autoComplete="username"
              autoFocus
              name="username"
              onChange={handleChange}
              required
              type="text"
              value={form.username}
            />
          </label>

          <label>
            Mot de passe
            <input
              autoComplete="current-password"
              name="password"
              onChange={handleChange}
              required
              type="password"
              value={form.password}
            />
          </label>

          {error && <div className="form-error">{error}</div>}

          <button className="login-button" disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Verification' : 'Se connecter'}
          </button>
        </form>
      </section>
    </main>
  )
}

export default LoginPage
