/**
 * API Service for Football Prediction Backend
 */
import axios from 'axios';

// In development, use empty string to leverage Vite proxy
// In production, use VITE_API_URL environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
});

// Request interceptor
apiClient.interceptors.request.use(
    (config) => {
        // Add any auth tokens here if needed in the future
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            // Server responded with error
            console.error('API Error:', error.response.data);
        } else if (error.request) {
            // No response received
            console.error('Network Error:', error.message);
        }
        return Promise.reject(error);
    }
);

// API Methods
export const api = {
    // Health check
    healthCheck: () => apiClient.get('/api/health'),

    // Leagues
    getLeagues: () => apiClient.get('/api/leagues'),
    getLeagueTeams: (leagueId) => apiClient.get(`/api/leagues/${leagueId}/teams`),
    getLeagueMatches: (leagueId, params = {}) =>
        apiClient.get(`/api/leagues/${leagueId}/matches`, { params }),

    // Teams
    getTeam: (teamId) => apiClient.get(`/api/teams/${teamId}`),

    // Matches
    getMatch: (matchId) => apiClient.get(`/api/matches/${matchId}`),
    getMatchPrediction: (matchId) => apiClient.get(`/api/matches/${matchId}/prediction`),

    // Predictions
    getUpcomingPredictions: (params = {}) =>
        apiClient.get('/api/predictions/upcoming', { params }),
    getTopPredictionsByLeague: (params = {}) =>
        apiClient.get('/api/predictions/top-by-league', { params }),

    // ML Predictions
    predictMatch: (matchData) =>
        apiClient.post('/api/predict/match', matchData),
    generateUpcomingPredictions: (params = {}) =>
        apiClient.post('/api/predict/upcoming', null, { params }),

    // Statistics
    getModelPerformance: (params = {}) =>
        apiClient.get('/api/stats/model-performance', { params }),
    getAccuracyStats: () => apiClient.get('/api/stats/accuracy'),

    // Accuracy Statistics (new)
    getAccuracyOverall: () => apiClient.get('/api/stats/accuracy/overall'),
    getAccuracyByBetType: () => apiClient.get('/api/stats/accuracy/by-bet-type'),
    getAccuracyHistory: (params = {}) => apiClient.get('/api/stats/accuracy/history', { params }),
    getPredictionsWithResults: (params = {}) => apiClient.get('/api/predictions/with-results', { params }),
};

export default apiClient;
