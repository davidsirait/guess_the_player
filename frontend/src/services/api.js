import axios from 'axios';

// Get API URL from environment variable with fallback
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

console.log('API URL:', API_URL); // For debugging

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add request interceptor for logging (only in development)
if (import.meta.env.DEV) {
  api.interceptors.request.use(
    (config) => {
      console.log('API Request:', config.method.toUpperCase(), config.url);
      return config;
    },
    (error) => {
      console.error('API Request Error:', error);
      return Promise.reject(error);
    }
  );
}

// Add response interceptor for logging and error handling
api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log('API Response:', response.status, response.config.url);
    }
    return response;
  },
  (error) => {
    // Log errors in development
    if (import.meta.env.DEV) {
      console.error('API Error:', error.response?.status, error.config?.url);
      console.error('Error details:', error.response?.data);
    }
    
    // Handle network errors
    if (!error.response) {
      console.error('Network error - backend might be down');
    }
    
    return Promise.reject(error);
  }
);

// Session API calls
export const sessionAPI = {
  // Start a new game session
  startSession: async (difficulty, topN) => {
    const response = await api.post('/session/start', {
      difficulty,
      top_n: topN,
    });
    return response.data;
  },

  // Submit a guess
  submitGuess: async (sessionId, guess) => {
    const response = await api.post(`/session/${sessionId}/guess`, {
      guess,
    });
    return response.data;
  },

  // Get next question
  getNextQuestion: async (sessionId, difficulty = null, topN = null) => {
    const body = {};
    if (difficulty) body.difficulty = difficulty;
    if (topN) body.top_n = topN;
    
    const response = await api.post(`/session/${sessionId}/next`, body);
    return response.data;
  },

  // End session
  endSession: async (sessionId) => {
    const response = await api.delete(`/session/${sessionId}`);
    return response.data;
  },

  // Get session status
  getStatus: async (sessionId) => {
    const response = await api.get(`/session/${sessionId}/status`);
    return response.data;
  },
};

// Game stats API
export const gameAPI = {
  getStats: async () => {
    const response = await api.get('/game/stats');
    return response.data;
  },
};

export default api;