import './LoadingSkeleton.css'

function LoadingSkeleton({ type = 'card', count = 3 }) {
  if (type === 'card') {
    return (
      <div className="skeleton-grid">
        {[...Array(count)].map((_, i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton-header">
              <div className="skeleton-title"></div>
              <div className="skeleton-circle"></div>
            </div>
            <div className="skeleton-body">
              <div className="skeleton-badge"></div>
              <div className="skeleton-badge"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (type === 'table') {
    return (
      <div className="skeleton-table">
        <div className="skeleton-row header">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton-cell"></div>
          ))}
        </div>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="skeleton-row">
            {[...Array(4)].map((_, j) => (
              <div key={j} className="skeleton-cell"></div>
            ))}
          </div>
        ))}
      </div>
    )
  }

  return null
}

export default LoadingSkeleton
