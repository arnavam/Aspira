import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './pages/Auth';
import Setup from './pages/Setup';
import Interview from './pages/Interview';
import Dashboard from './pages/Dashboard';
import KnowledgeMap from './pages/KnowledgeMap';
import { getAuthToken } from './services/api';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = getAuthToken();
  const isAuthenticated = token && token !== 'undefined' && token !== 'null' && token.length > 5;
  if (!isAuthenticated) return <Navigate to="/" replace />;
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Auth />} />
        
        <Route 
          path="/setup" 
          element={
            <ProtectedRoute>
              <Setup />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/interview" 
          element={
            <ProtectedRoute>
              <Interview />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/dashboard/:id" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/knowledge-map/:id" 
          element={
            <ProtectedRoute>
              <KnowledgeMap />
            </ProtectedRoute>
          } 
        />
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
