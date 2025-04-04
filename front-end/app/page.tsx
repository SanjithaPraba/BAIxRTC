import { Pencil } from "lucide-react"
import "./styles.css"

export default function SlackbotSettings() {
  return (
    <div className="container">
      <div className="content">
        <h1 className="title">Member Support Slackbot Settings</h1>

        <div className="divider"></div>

        {/* Current Data State Section */}
        <section className="section">
          <h2 className="section-title">Current Data State</h2>

          <div className="card-grid">
            <div className="card">
              <p className="card-title">Last Upload</p>
              <p className="card-value">XX/XX/XX</p>
            </div>

            <div className="card">
              <p className="card-title">Stored Messages From</p>
              <p className="card-value">XX/XX/XX - XX/XX/XX</p>
            </div>

            <div className="card">
              <p className="card-title">AWS Storage Usage</p>
              <p className="card-value">XX MB / XX MB</p>
            </div>

            <div className="card">
              <p className="card-title">ChromaDB Storage Usage</p>
              <p className="card-value">XX MB / XX MB</p>
            </div>
          </div>
        </section>

        <div className="divider"></div>

        {/* Update Data Section */}
        <section className="section">
          <h2 className="section-title">Update Data</h2>

          <div className="update-data-container">
            <div className="update-data-column">
              <p className="item-title">Manually  JSON exports</p>
              <input type="file"/>

              <div className="toggle-container">
                <div className="toggle-header">
                  <p className="item-title">Automatically upload messages real-time</p>
                  <label className="toggle">
                      <input type="checkbox" />
                      <span className="toggle-slider"></span>
                  </label>
                </div>
                <p className="toggle-description">When disabled, all updates happen after a manual upload</p>
              </div>
            </div>

            <div className="update-data-column">
              <p className="item-title">Delete Data</p>

              <div className="date-inputs">
                <div className="date-input-group">
                  <p className="date-label">From:</p>
                  <input type="date" className="date-input" placeholder="mm/dd/yyyy" />
                </div>
                <div className="date-input-group">
                  <p className="date-label">To:</p>
                  <input type="date" className="date-input" placeholder="mm/dd/yyyy" />
                </div>
              </div>

            </div>
          </div>
        </section>

        <div className="divider"></div>

        {/* Update Task Escalation Section */}
        <section className="section">
          <h2 className="section-title">Update Task Escalation</h2>

          <button className="button button-edit">
            Edit Staff Information <Pencil size={16} className="pencil-icon" />
          </button>

          <div className="staff-info">
            <p className="staff-name">Jane Doe</p>
            <p className="staff-tasks">Tasks: Member Support, Scholarships</p>
          </div>
        </section>

        <div className="submit-container">
          <button className="button button-primary">SUBMIT CHANGES</button>
        </div>
      </div>
    </div>
  )
}

