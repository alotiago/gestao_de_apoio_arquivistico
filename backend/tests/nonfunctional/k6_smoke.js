import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
const authUsername = __ENV.AUTH_USERNAME;
const authPassword = __ENV.AUTH_PASSWORD;
const providedToken = __ENV.ACCESS_TOKEN;

export const options = {
  scenarios: {
    smoke_load: {
      executor: 'ramping-vus',
      stages: [
        { duration: '30s', target: 5 },
        { duration: '1m', target: 10 },
        { duration: '30s', target: 0 },
      ],
      gracefulRampDown: '10s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.03'],
    http_req_duration: ['p(95)<800', 'p(99)<1500'],
    'http_req_duration{endpoint:health}': ['p(95)<300'],
    'http_req_duration{endpoint:ready}': ['p(95)<400'],
    'http_req_duration{endpoint:metrics_summary}': ['p(95)<500'],
    'http_req_duration{endpoint:health_smoke}': ['p(95)<1200'],
  },
};

function loginAndGetToken() {
  if (!authUsername || !authPassword) {
    return null;
  }

  const payload = {
    username: authUsername,
    password: authPassword,
  };

  const response = http.post(`${baseUrl}/api/v1/auth/login`, payload, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    tags: { endpoint: 'auth_login' },
  });

  if (response.status !== 200) {
    return null;
  }

  const parsed = response.json();
  return parsed?.access_token || null;
}

export function setup() {
  if (providedToken) {
    return { token: providedToken };
  }

  const token = loginAndGetToken();
  return { token };
}

export default function (data) {
  const healthResponse = http.get(`${baseUrl}/health`, { tags: { endpoint: 'health' } });
  check(healthResponse, {
    'health status 200': (response) => response.status === 200,
    'health body has status': (response) => response.json()?.status === 'healthy',
  });

  const readyResponse = http.get(`${baseUrl}/ready`, { tags: { endpoint: 'ready' } });
  check(readyResponse, {
    'ready status 200': (response) => response.status === 200,
    'ready body has status': (response) => response.json()?.status === 'ready',
  });

  const metricsResponse = http.get(`${baseUrl}/metrics/summary`, { tags: { endpoint: 'metrics_summary' } });
  check(metricsResponse, {
    'metrics status 200': (response) => response.status === 200,
  });

  if (data.token) {
    const smokeResponse = http.get(`${baseUrl}/health/smoke`, {
      headers: { Authorization: `Bearer ${data.token}` },
      tags: { endpoint: 'health_smoke' },
    });

    check(smokeResponse, {
      'smoke status 200': (response) => response.status === 200,
      'smoke overall status valid': (response) => {
        const overallStatus = response.json()?.overall_status;
        return overallStatus === 'ok' || overallStatus === 'degraded';
      },
    });
  }

  sleep(1);
}