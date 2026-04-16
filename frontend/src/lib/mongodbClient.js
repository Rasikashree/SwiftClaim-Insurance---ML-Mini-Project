/**
 * MongoDB API Client
 * ────────────────────────────
 * Frontend API client for MongoDB operations through the Flask backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * High-level MongoDB operations through the backend API
 */
export const MongoDB = {
  // ─────── USERS ──────────────────────────────────────────
  async createUser(userData) {
    const { data } = await api.post('/users', userData);
    return data;
  },

  async getUser(userId) {
    const { data } = await api.get(`/users/${userId}`);
    return data;
  },

  async getUserByEmail(email) {
    const { data } = await api.get('/users/email', { params: { email } });
    return data;
  },

  async updateUser(userId, updates) {
    const { data } = await api.put(`/users/${userId}`, updates);
    return data;
  },

  async deleteUser(userId) {
    const { data } = await api.delete(`/users/${userId}`);
    return data;
  },

  // ─────── CLAIMS ──────────────────────────────────────────
  async createClaim(userId, claimData) {
    const { data } = await api.post('/claims', {
      user_id: userId,
      ...claimData,
    });
    return data;
  },

  async getClaim(claimId) {
    const { data } = await api.get(`/claims/${claimId}`);
    return data;
  },

  async getUserClaims(userId) {
    const { data } = await api.get('/claims/user', { params: { user_id: userId } });
    return data;
  },

  async getClaimsByStatus(status) {
    const { data } = await api.get('/claims/status', { params: { status } });
    return data;
  },

  async updateClaim(claimId, updates) {
    const { data } = await api.put(`/claims/${claimId}`, updates);
    return data;
  },

  async deleteClaim(claimId) {
    const { data } = await api.delete(`/claims/${claimId}`);
    return data;
  },

  // ─────── DAMAGE ASSESSMENTS ──────────────────────────────
  async createAssessment(claimId, assessmentData) {
    const { data } = await api.post('/assessments', {
      claim_id: claimId,
      ...assessmentData,
    });
    return data;
  },

  async getAssessment(assessmentId) {
    const { data } = await api.get(`/assessments/${assessmentId}`);
    return data;
  },

  async getClaimAssessments(claimId) {
    const { data } = await api.get('/assessments/claim', {
      params: { claim_id: claimId },
    });
    return data;
  },

  async updateAssessment(assessmentId, updates) {
    const { data } = await api.put(`/assessments/${assessmentId}`, updates);
    return data;
  },

  async deleteAssessment(assessmentId) {
    const { data } = await api.delete(`/assessments/${assessmentId}`);
    return data;
  },

  // ─────── PAYOUTS ────────────────────────────────────────
  async createPayout(claimId, payoutData) {
    const { data } = await api.post('/payouts', {
      claim_id: claimId,
      ...payoutData,
    });
    return data;
  },

  async getPayout(payoutId) {
    const { data } = await api.get(`/payouts/${payoutId}`);
    return data;
  },

  async getClaimPayout(claimId) {
    const { data } = await api.get('/payouts/claim', {
      params: { claim_id: claimId },
    });
    return data;
  },

  async updatePayout(payoutId, updates) {
    const { data } = await api.put(`/payouts/${payoutId}`, updates);
    return data;
  },

  async getPayoutsByStatus(status) {
    const { data } = await api.get('/payouts/status', { params: { status } });
    return data;
  },

  // ─────── PARTS ──────────────────────────────────────────
  async createPart(partData) {
    const { data } = await api.post('/parts', partData);
    return data;
  },

  async getPart(partId) {
    const { data } = await api.get(`/parts/${partId}`);
    return data;
  },

  async getPartByName(partName) {
    const { data } = await api.get('/parts/name', { params: { name: partName } });
    return data;
  },

  async getAllParts() {
    const { data } = await api.get('/parts');
    return data;
  },

  async updatePart(partId, updates) {
    const { data } = await api.put(`/parts/${partId}`, updates);
    return data;
  },

  async deletePart(partId) {
    const { data } = await api.delete(`/parts/${partId}`);
    return data;
  },

  // ─────── ANALYTICS ──────────────────────────────────────
  async getClaimsStatistics() {
    const { data } = await api.get('/analytics/claims-stats');
    return data;
  },

  async getUserClaimsCount(userId) {
    const { data } = await api.get('/analytics/user-claims-count', {
      params: { user_id: userId },
    });
    return data;
  },

  async getTotalPayouts() {
    const { data } = await api.get('/analytics/total-payouts');
    return data;
  },
};

export default MongoDB;
