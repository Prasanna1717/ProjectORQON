import React from 'react'
import ReactDOM from 'react-dom/client'
import './carbon.scss'
import './index.css'
console.log('🚀 main.jsx loaded');
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error('❌ React Error Boundary caught:', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', background: '#da1e28', color: 'white', fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
          <h1>⚠️ Application Error</h1>
          <h2>{this.state.error?.toString()}</h2>
          <pre style={{ background: 'rgba(0,0,0,0.3)', padding: '20px', overflow: 'auto', fontSize: '14px' }}>
            {this.state.error?.stack}
          </pre>
          <button onClick={() => window.location.reload()} style={{ padding: '10px 20px', fontSize: '16px', marginTop: '20px', cursor: 'pointer' }}>
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
let App;
try {
  const module = await import('./App.jsx');
  App = module.default;
  console.log('✅ App imported successfully');
} catch (error) {
  console.error('❌ Failed to import App:', error);
  App = () => (
    <div style={{ padding: '40px', background: '#da1e28', color: 'white' }}>
      <h1>Failed to load App component</h1>
      <p>{error.message}</p>
      <pre style={{ background: 'rgba(0,0,0,0.2)', padding: '10px' }}>{error.stack}</pre>
    </div>
  );
}
const root = document.getElementById('root');
if (!root) {
  document.body.innerHTML = '<h1 style="color:red;padding:40px;">Error: Root element not found!</h1>';
} else {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>,
  );
  console.log('✅ App rendered');
}
