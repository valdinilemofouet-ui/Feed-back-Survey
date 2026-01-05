import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';

// Components
import Navbar from './components/layout/Navbar';
import PrivateRoute from './components/layout/PrivateRoute';
import PublicRoute from './components/layout/PublicRoute'; // <--- NOUVEL IMPORT
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Dashboard from './components/dashboard/Dashboard';
import SurveyForm from './components/survey/SurveyForm';
import TakeSurvey from './components/survey/TakeSurvey';
import SurveyResults from './components/survey/SurveyResults';
import Profile from './components/profile/Profile';

import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Navbar />
          <main className="main-content">
            <Routes>
              {/* --- Routes Accessibles à tous (Public) --- */}
              <Route path="/" element={<Navigate to="/dashboard" />} />
              <Route path="/survey/:surveyId" element={<TakeSurvey />} />

              {/* --- Routes "Anonymes" (Accessibles UNIQUEMENT si NON connecté) --- */}
              {/* Si l'utilisateur est déjà connecté, il sera redirigé vers le Dashboard */}
              <Route path="/login" element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              } />
              
              <Route path="/register" element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              } />

              {/* --- Routes Protégées (Accessibles UNIQUEMENT si connecté) --- */}
              <Route path="/dashboard" element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              } />
              
              <Route path="/surveys/create" element={
                <PrivateRoute>
                  <SurveyForm />
                </PrivateRoute>
              } />
              
              <Route path="/surveys/:surveyId/results" element={
                <PrivateRoute>
                  <SurveyResults />
                </PrivateRoute>
              } />
              
              <Route path="/profile" element={
                <PrivateRoute>
                  <Profile />
                </PrivateRoute>
              } />

              {/* --- Fallback (Erreur 404) --- */}
              <Route path="*" element={<Navigate to="/dashboard" />} />
            </Routes>
          </main>
          
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 3000,
              style: {
                background: '#333',
                color: '#fff',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;