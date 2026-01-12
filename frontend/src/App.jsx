import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Gallery from './pages/Gallery';
import JobDetail from './pages/JobDetail';

function App() {
  return (
    <BrowserRouter>
      <div className="w-full min-h-screen bg-surface-dim">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/job/:jobId" element={<JobDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
