import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import AddPersonPage from './pages/AddPersonPage';
import MissingPersonsPage from './pages/MissingPersonsPage';
import PersonDetailPage from './pages/PersonDetailPage';
import UploadVideoPage from './pages/UploadVideoPage';
import ResultsPage from './pages/ResultsPage';
import LiveMonitoringPage from './pages/LiveMonitoringPage';

export default function App() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />}
      />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/add-person" element={<ProtectedRoute><AddPersonPage /></ProtectedRoute>} />
      <Route path="/missing-persons" element={<ProtectedRoute><MissingPersonsPage /></ProtectedRoute>} />
      <Route path="/person/:id" element={<ProtectedRoute><PersonDetailPage /></ProtectedRoute>} />
      <Route path="/upload-video" element={<ProtectedRoute><UploadVideoPage /></ProtectedRoute>} />
      <Route path="/results" element={<ProtectedRoute><ResultsPage /></ProtectedRoute>} />
      <Route path="/live-monitoring" element={<ProtectedRoute><LiveMonitoringPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to={user ? '/dashboard' : '/login'} replace />} />
    </Routes>
  );
}
