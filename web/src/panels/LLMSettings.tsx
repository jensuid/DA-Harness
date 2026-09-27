// W2X-012 phase B: the settings surface that puts the credential where the
// packaged core can read it.
//
// Phase A named the state - the banner says the LLM is not configured, and
// points at DAH_LLM_API_KEY. This is the surface that changes it. The
// packaged app cannot read a `.env` that was never bundled, so the key arrives
// as a file in the data directory the shell already points the core at, and
// this form is how it gets there.
//
// The shell opens it with an evaluated script that posts an event, the same
// channel the update notice uses - no Tauri command, so the capability set
// stays empty on purpose. A browser host never receives the event, because a
// browser has no menu bar; the panel itself is an ordinary form posting to an
// ordinary endpoint, so the browser host gets the same surface if it ever
// needs one.
//
// The three fields are the three the core reads. Model and base URL are
// optional and show the core's public defaults as placeholders, because those
// defaults are the ones the adapters hold; the key is the one that matters,
// and an empty key is a cleared setting, not an empty value the core would try
// to authenticate with.

import { useEffect, useState } from 'react'
import { getLlmConfig, putLlmConfig, type LlmConfig, type LlmStatus } from '../api'
import { SETTINGS_EVENT, LLM_CHANGED_EVENT } from '../shell'
import { Button } from '../lib/ui'

type Phase = 'closed' | 'loading' | 'ready' | 'saving' | 'saved' | 'error'

export function LlmSettingsPanel() {
  const [phase, setPhase] = useState<Phase>('closed')
  const [config, setConfig] = useState<LlmConfig>({ api_key: '', model: '', base_url: '' })
  const [error, setError] = useState<string | null>(null)
  const [savedStatus, setSavedStatus] = useState<LlmStatus | null>(null)

  // The shell dispatches this event from the menu bar; a browser host never
  // receives it, so the panel stays closed there unless something else opens
  // it. Read once per open, never polled: the settings are a property of the
  // deployment, not a live value.
  useEffect(() => {
    const open = () => {
      setPhase('loading')
      setError(null)
      setSavedStatus(null)
      void getLlmConfig()
        .then((value) => {
          setConfig(value)
          setPhase('ready')
        })
        .catch((reason) => {
          setError(reason instanceof Error ? reason.message : String(reason))
          // An unreadable state is still a state the analyst can write over:
          // the panel opens with blanks rather than refusing to appear, and
          // a save is how the analyst fixes a corrupt file.
          setConfig({ api_key: '', model: '', base_url: '' })
          setPhase('ready')
        })
    }
    window.addEventListener(SETTINGS_EVENT, open as EventListener)
    return () => window.removeEventListener(SETTINGS_EVENT, open as EventListener)
  }, [])

  // Closed is the resting state: the panel is not a banner, and an empty
  // form on every screen is the same noise phase A refused to make.
  if (phase === 'closed') return null

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    setPhase('saving')
    setError(null)
    setSavedStatus(null)
    void putLlmConfig(config)
      .then((status) => {
        setSavedStatus(status)
        setPhase('saved')
        // Tell the banner to refetch. The panel is usually the thing that
        // opened from the banner, and a banner that keeps showing a concern
        // the analyst just resolved is a banner that stops being believed.
        window.dispatchEvent(new CustomEvent(LLM_CHANGED_EVENT))
      })
      .catch((reason) => {
        setError(reason instanceof Error ? reason.message : String(reason))
        // Back to ready, not closed: the analyst's typed values stay in the
        // form, so a network blip does not cost them the key they entered.
        setPhase('ready')
      })
  }

  return (
    <div className="llm-settings" role="dialog" aria-label="DAH settings">
      <form onSubmit={submit}>
        <h2>DAH Settings</h2>
        <p className="llm-settings-lede">
          The key lives in a file beside your cases, not in the application -
          DAH never sends it anywhere but the model provider, and clearing the
          field clears the setting.
        </p>
        <label className="llm-settings-field">
          <span>API key</span>
          <input
            type="password"
            name="api_key"
            autoComplete="off"
            spellCheck={false}
            value={config.api_key}
            onChange={(event) => setConfig({ ...config, api_key: event.target.value })}
            placeholder="sk-…"
          />
        </label>
        <label className="llm-settings-field">
          <span>Model</span>
          <input
            type="text"
            name="model"
            autoComplete="off"
            spellCheck={false}
            value={config.model}
            onChange={(event) => setConfig({ ...config, model: event.target.value })}
            placeholder="gpt-4o-mini"
          />
        </label>
        <label className="llm-settings-field">
          <span>Base URL</span>
          <input
            type="text"
            name="base_url"
            autoComplete="off"
            spellCheck={false}
            value={config.base_url}
            onChange={(event) => setConfig({ ...config, base_url: event.target.value })}
            placeholder="https://api.openai.com/v1"
          />
        </label>
        <div className="llm-settings-actions">
          <Button type="submit" disabled={phase === 'saving'}>
            {phase === 'saving' ? 'Saving…' : 'Save'}
          </Button>
          <Button type="button" variant="link" onClick={() => setPhase('closed')}>
            Close
          </Button>
        </div>
        {phase === 'saved' && savedStatus?.configured && (
          <p className="llm-settings-saved" role="status">
            Saved. The LLM features will use it now - no restart needed.
          </p>
        )}
        {phase === 'saved' && !savedStatus?.configured && (
          // The save landed but the state is still unconfigured. That is
          // worth saying as a sentence rather than as a green tick: the
          // analyst cleared the key, or the core could not read it.
          <p className="llm-settings-saved" role="status">
            Saved, but the core still reports the LLM is not configured - check
            the key is not blank.
          </p>
        )}
        {error && (
          <p className="llm-settings-error" role="alert">
            {error}
          </p>
        )}
      </form>
    </div>
  )
}
