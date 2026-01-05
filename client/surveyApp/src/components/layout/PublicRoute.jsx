// src/components/layout/PublicRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext'; // Assurez-vous que le chemin est bon

const PublicRoute = ({ children }) => {
  const { currentUser, loading } = useAuth(); // Adaptez 'currentUser' selon votre Context (ex: 'user')

  // Optionnel : afficher un chargement si l'auth n'est pas encore vérifiée
  if (loading) {
    return <div>Chargement...</div>; 
  }

  // Si l'utilisateur est connecté, on le redirige vers le dashboard
  if (currentUser) {
    return <Navigate to="/dashboard" replace />;
  }

  // Sinon, on affiche la page demandée (Login ou Register)
  return children;
};

export default PublicRoute;