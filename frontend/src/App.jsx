import { useState } from 'react'
import './App.css'

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
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Something went wrong')
      }
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>NexTrip - AI Trip Planner</h1>

      <form onSubmit={handleSubmit} className="trip-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="from_location">From Location *</label>
            <input
              type="text"
              id="from_location"
              name="from_location"
              value={formData.from_location}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="to_location">To Location *</label>
            <input
              type="text"
              id="to_location"
              name="to_location"
              value={formData.to_location}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="travel_date">Travel Date *</label>
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
            <label htmlFor="return_date">Return Date</label>
            <input
              type="date"
              id="return_date"
              name="return_date"
              value={formData.return_date}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="num_days">Number of Days</label>
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
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="cabin_class">Cabin Class</label>
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
              <option value="INR">INR</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
            </select>
          </div>
        </div>

        <div className="form-row checkbox-row">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="include_hotels"
              checked={formData.include_hotels}
              onChange={handleChange}
            />
            Include Hotels
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="include_rentals"
              checked={formData.include_rentals}
              onChange={handleChange}
            />
            Include Car Rentals
          </label>
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Planning Trip...' : 'Plan Trip'}
        </button>
      </form>

      {error && (
        <div className="error-box">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="result-box">
          <h2>Trip Plan</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default App
