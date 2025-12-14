import React from 'react';
import IncidentList from './components/IncidentList';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>🛡️ DLP Messenger Control</h1>
        <p>Система контроля утечек конфиденциальной информации</p>
      </header>

      <main className="app-main">
        <IncidentList />
      </main>

      <footer className="app-footer">
        <p>© 2025 DLP Messenger Control. Версия 1.0.0</p>
      </footer>
    </div>
  );
}

export default App;
