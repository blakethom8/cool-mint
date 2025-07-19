import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { HomePage } from './pages/HomePage';
import { ActivitySelector } from './pages/ActivitySelector';
import { BundleManagement } from './pages/BundleManagement';
import MarketExplorer from './pages/MarketExplorer';
import './App.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="app-layout">
      <Navigation />
      <div className="app-main">
        {children}
      </div>
    </div>
  );
};

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/activities" element={<ActivitySelector />} />
          <Route path="/bundles" element={<BundleManagement />} />
          <Route path="/bundles/:bundleId" element={<BundleManagement />} />
          <Route path="/contacts" element={<MarketExplorer />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;