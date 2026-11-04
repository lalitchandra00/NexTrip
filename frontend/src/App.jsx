import { useState } from 'react'
import './App.css'

const toRenderableText = (value) => {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) return value.map(toRenderableText).join('\n')
  if (typeof value === 'object') {
    if (typeof value.text === 'string') return value.text
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const TRANSPORT_LABELS = {
  train: 'Trains',
  flight: 'Flights',
  bus: 'Buses',
  car: 'Car rentals',
}

const TRANSPORT_ICONS = {
  train: '🚆',
  flight: '✈️',
  bus: '🚌',
  car: '🚗',
}

function TransportSection({ transport }) {
  const legs = Object.entries(transport?.legs || {})
    .filter(([, leg]) => leg)
    .map(([mode, leg]) => ({ mode, ...leg }))
  if (!legs.length) return null

  return (
    <div className="transport-section">
      <h2>Getting there</h2>
      <p className="transport-route">
        {toRenderableText(transport.from)} → {toRenderableText(transport.to)}
        {transport.date ? ` · ${toRenderableText(transport.date)}` : ''}
      </p>
      <div className="transport-grid">
        {legs.map((leg) => (
          <div key={leg.mode} className="transport-card">
            <div className="transport-card-header">
              <span className="transport-icon">{TRANSPORT_ICONS[leg.mode] || '🧭'}</span>
              <h3>{TRANSPORT_LABELS[leg.mode] || leg.mode}</h3>
            </div>
            {leg.options?.length > 0 ? (
              <ul className="transport-options">
                {leg.options.map((option, index) => (
                  <li key={`${leg.mode}-${index}`}>
                    <div className="transport-option-head">
                      <strong>{toRenderableText(option.title)}</strong>
                      {option.price ? (
                        <span className="transport-price">{toRenderableText(option.price)}</span>
                      ) : null}
                    </div>
                    {option.subtitle ? (
                      <span className="transport-subtitle">{toRenderableText(option.subtitle)}</span>
                    ) : null}
                    <div className="transport-meta">
                      {option.depart && (
                        <span>
                          {toRenderableText(option.depart)}
                          {option.from ? ` · ${toRenderableText(option.from)}` : ''}
                        </span>
                      )}
                      {option.arrive && (
                        <span>
                          {toRenderableText(option.arrive)}
                          {option.to ? ` · ${toRenderableText(option.to)}` : ''}
                        </span>
                      )}
                      {option.duration && <span>{toRenderableText(option.duration)}</span>}
                      {option.meta && <span>{toRenderableText(option.meta)}</span>}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="transport-empty">{toRenderableText(leg.error) || 'No options found.'}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function App() {
  const [formData, setFormData] = useState({
    from_location: '',
    to_location: '',
    travel_date: '',
    num_days: 1,
    return_date: '',
    adults: 1,
    cabin_class: 'economy',
    currency: 'INR',
    include_hotels: true,
    include_rentals: false,
    country_of_residence: 'in'
  })

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : type === 'number' ? Number(value) : value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/plan-trip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Something went wrong')
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <header className="app-header">
        <span className="app-badge">AI Trip Planner</span>
        <h1>Nex<span>Trip</span></h1>
        <p className="app-subtitle">
          Transport, places, stays, and weather — planned together.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="trip-form">
        <div className="form-heading">
          <h2>Plan your trip</h2>
          <p>Fill in the details and let AI do the rest.</p>
        </div>

        {/* ── Route ── */}
        <p className="form-section-label"><span>📍</span> Route</p>
        <div className="route-row">
          <div className="form-group">
            <label htmlFor="from_location">From</label>
            <div className="input-icon-wrap">
              <span className="input-icon">🛫</span>
              <input
                type="text"
                id="from_location"
                name="from_location"
                placeholder="Departure city"
                value={formData.from_location}
                onChange={handleChange}
                required
              />
            </div>
          </div>
          <span className="route-arrow">→</span>
          <div className="form-group">
            <label htmlFor="to_location">To</label>
            <div className="input-icon-wrap">
              <span className="input-icon">🛬</span>
              <input
                type="text"
                id="to_location"
                name="to_location"
                placeholder="Destination city"
                value={formData.to_location}
                onChange={handleChange}
                required
              />
            </div>
          </div>
        </div>

        {/* ── Dates ── */}
        <p className="form-section-label"><span>📅</span> Dates</p>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="travel_date">
              Departure date <span className="required-star">*</span>
            </label>
            <input
              type="date"
              id="travel_date"
              name="travel_date"
              value={formData.travel_date}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="return_date">
              Return date <span className="optional-tag">optional</span>
            </label>
            <input
              type="date"
              id="return_date"
              name="return_date"
              value={formData.return_date}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* ── Travellers & Preferences ── */}
        <p className="form-section-label"><span>🧳</span> Travellers &amp; Preferences</p>
        <div className="form-row form-row-4">
          <div className="form-group">
            <label htmlFor="num_days">Days</label>
            <input
              type="number"
              id="num_days"
              name="num_days"
              min="1"
              value={formData.num_days}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="adults">Adults</label>
            <input
              type="number"
              id="adults"
              name="adults"
              min="1"
              value={formData.adults}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="cabin_class">Cabin class</label>
            <select
              id="cabin_class"
              name="cabin_class"
              value={formData.cabin_class}
              onChange={handleChange}
            >
              <option value="economy">Economy</option>
              <option value="premium_economy">Premium Economy</option>
              <option value="business">Business</option>
              <option value="first">First</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="currency">Currency</label>
            <select
              id="currency"
              name="currency"
              value={formData.currency}
              onChange={handleChange}
            >
              <option value="INR">🇮🇳 INR</option>
              <option value="USD">🇺🇸 USD</option>
              <option value="EUR">🇪🇺 EUR</option>
            </select>
          </div>
        </div>

        {/* ── Add-ons ── */}
        <p className="form-section-label"><span>➕</span> Add-ons</p>
        <div className="checkbox-row">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="include_hotels"
              checked={formData.include_hotels}
              onChange={handleChange}
            />
            🏨 Hotels
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="include_rentals"
              checked={formData.include_rentals}
              onChange={handleChange}
            />
            🚗 Car Rentals
          </label>
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? '⏳ Planning your trip…' : '✈ Plan My Trip'}
        </button>
      </form>

      {loading && (
        <div className="loading-note">
          <span className="loading-dot" />
          Searching transport, places, and weather...
        </div>
      )}

      {error && (
        <div className="error-box">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="result-box">
          {result.error && (
            <p className="result-warning">
              Some travel details could not be loaded: {result.error}
            </p>
          )}
          {result.itinerary?.error && (
            <p className="result-warning">{result.itinerary.error}</p>
          )}
          {result.itinerary?.days?.length > 0 ? (
            <>
              <h2>Day-by-Day Itinerary</h2>
              <div className="trip-summary">
                <div className="summary-item">
                  <span>Destination</span>
                  <strong>{result.itinerary.destination}</strong>
                </div>
                <div className="summary-item">
                  <span>Duration</span>
                  <strong>
                    {result.itinerary.num_days} day
                    {result.itinerary.num_days !== 1 ? 's' : ''}
                  </strong>
                </div>
                <div className="summary-item">
                  <span>Places</span>
                  <strong>{result.itinerary.places?.length || 0}</strong>
                </div>
                {result.itinerary.days?.[0]?.date && (
                  <div className="summary-item">
                    <span>Dates</span>
                    <strong>
                      {result.itinerary.days[0].date}
                      {result.itinerary.days.length > 1
                        ? ` – ${result.itinerary.days[result.itinerary.days.length - 1].date}`
                        : ''}
                    </strong>
                  </div>
                )}
              </div>
              {result.itinerary.places?.length > 0 && (
                <div className="places-overview">
                  <h3>Places to visit</h3>
                  <ul className="places-list">
                    {result.itinerary.places.map((place) => (
                      <li key={place.name}>
                        <strong>{place.name}</strong>
                        {place.area && <span className="timeline-area">{place.area}</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="itinerary-days">
                {result.itinerary.days.map((day) => (
                  <div key={day.day} className="day-card">
                    <div className="day-header">
                      <span className="day-badge">Day {day.day}</span>
                      <div className="day-heading">
                        <h3>{day.title}</h3>
                        {day.date && <span className="day-date">{day.date}</span>}
                      </div>
                    </div>
                    {day.slots?.length ? (
                      <ul className="timeline">
                        {day.slots.map((slot, index) => (
                          <li
                            key={`${day.day}-${index}`}
                            className={`timeline-item ${slot.kind === 'break' ? 'timeline-break' : ''}`}
                          >
                            <span className="timeline-time">
                              {slot.start_time} – {slot.end_time}
                            </span>
                            <span className="timeline-dot" />
                            <div className="timeline-content">
                              <strong>{slot.place}</strong>
                              {slot.area && <span className="timeline-area">{slot.area}</span>}
                              {slot.notes && <p>{slot.notes}</p>}
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="free-day">Free day — explore at leisure.</p>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <h2>Trip Plan</h2>
          )}

          {result.transport && <TransportSection transport={result.transport} />}

          {result.result && (
            <details className="raw-result">
              <summary>Agent plan</summary>
              <pre>
                {toRenderableText(
                  typeof result.result === 'object' ? result.result.output ?? result.result : result.result
                )}
              </pre>
            </details>
          )}

          <details className="raw-result">
            <summary>Raw response</summary>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}

      <footer className="app-footer">
        NexTrip &middot; Plan less, travel more.
      </footer>
    </div>
  )
}

export default App
