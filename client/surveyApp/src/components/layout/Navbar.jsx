import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { LogOut, User, Home, PlusCircle } from 'lucide-react';
import aimsLogo from '../../assets/AIMS_logo.png';  // Import the logo

const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          <img src={aimsLogo} alt="AIMS Logo" className="logo-image" />
          <span>Survey App</span>
        </Link>

        {isAuthenticated ? (
          <div className="nav-menu">
            <Link to="/dashboard" className="nav-link">
              <Home size={18} />
              Dashboard
            </Link>
            <Link to="/surveys/create" className="nav-link">
              <PlusCircle size={18} />
              Create Survey
            </Link>
            <Link to="/profile" className="nav-link">
              <User size={18} />
              {user?.name}
            </Link>
            <button onClick={handleLogout} className="nav-link logout-btn">
              <LogOut size={18} />
              Logout
            </button>
          </div>
        ) : (
          <div className="nav-menu">
            <Link to="/login" className="nav-link">Login</Link>
            <Link to="/register" className="nav-link btn-primary">Register</Link>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;