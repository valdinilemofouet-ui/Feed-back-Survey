import axios from 'axios';

// --- START OF MODIFICATIONS ---

// 1. Get the Backend URL from environment variables (set in Render)
// 2. If the variable doesn't exist (e.g., on your PC), fallback to localhost.
const RAW_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// 3. Cleanup: Remove trailing slash if present to avoid errors like "//api"
const BASE_DOMAIN = RAW_URL.replace(/\/$/, '');

// 4. Append '/api' since that is your Flask route prefix
const API_BASE_URL = `${BASE_DOMAIN}/api`;

// --- END OF MODIFICATIONS ---

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests automatically
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle response errors globally
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Redirect to login only if not already on a public page
      if (!window.location.pathname.includes('/public/')) {
         window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// API Services
export const authAPI = {
  register: (data) => axiosInstance.post('/auth/register', data),
  login: (data) => axiosInstance.post('/auth/login', data)
};

export const surveyAPI = {
  create: (data) => axiosInstance.post('/surveys/', data),
  getMySurveys: () => axiosInstance.get('/surveys/'),
  getResults: (surveyId) => axiosInstance.get(`/surveys/${surveyId}/results`),
  deleteSurvey: (id) => axiosInstance.delete(`/surveys/${id}`),
  toggleStatus: (id) => axiosInstance.patch(`/surveys/${id}/status`),
};

export const publicAPI = {
  // Note: Using raw axios here to avoid interceptors (no token needed for public surveys)
  getSurvey: (surveyId) => axios.get(`${API_BASE_URL}/public/surveys/${surveyId}`),
  submitResponse: (id, data, config) => axiosInstance.post(`/public/surveys/${id}/respond`, data, config),
};

export default axiosInstance;