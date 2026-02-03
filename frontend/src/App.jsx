import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Gallery from './pages/Gallery';
import JobDetail from './pages/JobDetail';
import Properties from './pages/Properties';
import PropertyDetail from './pages/PropertyDetail';
import RoomDetail from './pages/RoomDetail';

function App() {
  return (
    <BrowserRouter>
      <div className="w-full min-h-screen bg-surface-dim">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/job/:jobId" element={<JobDetail />} />
          <Route path="/properties" element={<Properties />} />
          <Route path="/property/:propertyId" element={<PropertyDetail />} />
          <Route path="/room/:roomId" element={<RoomDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
