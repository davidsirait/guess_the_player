import axios from 'axios';

// Base URL - proxy handles routing to localhost:8000
const api = axios.create({
  baseURL: '/',
  headers: {
    'Content-Type': 'application/json',
  },
});

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