import axios from 'axios';

const STAFF_API_BASE = '/api/v1/staff-app';

const staffApi = axios.create({
  baseURL: STAFF_API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// ── Token 管理 ──
let staffAuth: { staffId: string; token: string } | null = null;

export function setStaffAuth(staffId: string, token: string) {
  staffAuth = { staffId, token };
  staffApi.defaults.headers['X-Staff-Token'] = token;
  localStorage.setItem('staff_id', staffId);
  localStorage.setItem('staff_token', token);
}

export function loadStaffAuth() {
  const staffId = localStorage.getItem('staff_id');
  const token = localStorage.getItem('staff_token');
  if (staffId && token) {
    staffAuth = { staffId, token };
    staffApi.defaults.headers['X-Staff-Token'] = token;
  }
  return staffAuth;
}

export function clearStaffAuth() {
  staffAuth = null;
  localStorage.removeItem('staff_id');
  localStorage.removeItem('staff_token');
  delete staffApi.defaults.headers['X-Staff-Token'];
}

export function getStaffAuth() {
  return staffAuth;
}

loadStaffAuth();

export default staffApi;
