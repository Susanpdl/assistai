// Passwordless login screen: email field -> "check your email" state.
// Follows 04-ui-guidelines (monochrome, single primary button, lots of whitespace).
import { useState } from 'react'
import { requestLink } from '../api/auth.js'

export default function LoginView() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  // The backend redirects here with ?auth=invalid when a link is bad/expired.
  const invalidLink = new URLSearchParams(window.location.search).get('auth') === 'invalid'

  async function onSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await requestLink(email.trim())
      setSent(true)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login">
      <div className="login__card">
        <div className="login__brand">AssistAI</div>

        {sent ? (
          <div>
            <h1 className="login__title">Check your email</h1>
            <p className="login__sub">
              If an account exists for <strong>{email}</strong>, a one-time sign-in link is on
              its way. It expires in 15 minutes.
            </p>
            <button className="btn btn--ghost login__submit" onClick={() => setSent(false)}>
              Use a different email
            </button>
          </div>
        ) : (
          <form onSubmit={onSubmit}>
            <h1 className="login__title">Sign in</h1>
            <p className="login__sub">
              We&apos;ll email you a one-time sign-in link — no password needed.
            </p>

            {invalidLink && (
              <p className="login__error">
                That sign-in link was invalid or expired. Request a new one below.
              </p>
            )}

            <label className="login__field">
              <span>Email</span>
              <input
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@school.edu"
              />
            </label>

            {error && <p className="login__error">{error}</p>}

            <button
              className="btn btn--primary login__submit"
              type="submit"
              disabled={submitting || !email.trim()}
            >
              {submitting ? 'Sending…' : 'Send me a link'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
