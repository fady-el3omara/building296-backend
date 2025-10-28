import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css'; // This includes Tailwind CSS

// React 18 uses createRoot instead of ReactDOM.render
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
