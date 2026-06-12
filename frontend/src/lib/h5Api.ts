import axios from 'axios';

/** H5 客户自助端 API 实例（面向终端客户，用 Token 而非 JWT） */
const h5Api = axios.create({
  baseURL: '/api/v1/h5',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

/**
 * 设置 H5 客户的 Token header（页面加载时调用一次）
 * @param customerId - 客户 UUID
 * @param token - HMAC token
 */
export function setH5Auth(customerId: string, token: string) {
  h5Api.defaults.headers.common['X-Customer-Token'] = token;
  // 也存下来，供构建 URL 时用
  localStorage.setItem('h5_customer_id', customerId);
  localStorage.setItem('h5_customer_token', token);
}

export function getH5CustomerId(): string {
  return localStorage.getItem('h5_customer_id') || '';
}

export function getH5Token(): string {
  return localStorage.getItem('h5_customer_token') || '';
}

export default h5Api;
