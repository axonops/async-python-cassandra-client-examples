import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { randomString, randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const errorRate = new Rate('errors');
const createUserDuration = new Trend('create_user_duration');
const getUserDuration = new Trend('get_user_duration');
const listUsersDuration = new Trend('list_users_duration');
const streamDuration = new Trend('stream_duration');

// Test configuration
export const options = {
  scenarios: {
    // Scenario 1: Gradual ramp-up
    gradual_ramp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },   // Ramp up to 10 users
        { duration: '1m', target: 50 },    // Ramp up to 50 users
        { duration: '3m', target: 50 },    // Stay at 50 users
        { duration: '1m', target: 100 },   // Ramp up to 100 users
        { duration: '3m', target: 100 },   // Stay at 100 users
        { duration: '1m', target: 0 },     // Ramp down
      ],
    },
    // Scenario 2: Spike test
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 5 },    // Warm up
        { duration: '5s', target: 200 },   // Spike to 200 users
        { duration: '30s', target: 200 },  // Stay at 200
        { duration: '5s', target: 5 },     // Back to normal
        { duration: '30s', target: 5 },    // Recovery period
      ],
      startTime: '5m',  // Start after gradual ramp
    },
    // Scenario 3: Constant load
    constant_load: {
      executor: 'constant-vus',
      vus: 25,
      duration: '10m',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests under 500ms
    errors: ['rate<0.1'],  // Error rate under 10%
    create_user_duration: ['p(95)<300'],
    get_user_duration: ['p(95)<100'],
  },
};

// Base URL - will be passed via --env BASE_URL=http://localhost:8001
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8001';

// Storage for created entities
const createdUsers = [];
const createdDocuments = [];

// Helper function to generate user data
function generateUserData() {
  return {
    id: `${Date.now()}-${randomString(8)}`,
    username: `user_${randomString(10)}`,
    email: `${randomString(8)}@example.com`,
    profile_data: {
      bio: randomString(100),
      age: randomIntBetween(18, 80),
      location: randomItem(['New York', 'London', 'Tokyo', 'Paris', 'Sydney']),
    },
  };
}

// Helper function to generate document data
function generateDocumentData() {
  return {
    id: `${Date.now()}-${randomString(8)}`,
    title: `Document ${randomString(10)}`,
    content: randomString(500),
    tags: Array.from({ length: randomIntBetween(1, 5) }, () => randomString(5)),
  };
}

export default function () {
  const scenario = randomIntBetween(1, 10);

  // 30% - Create user
  if (scenario <= 3) {
    const userData = generateUserData();
    const startTime = Date.now();
    
    const response = http.post(
      `${BASE_URL}/api/v1/users`,
      JSON.stringify(userData),
      {
        headers: { 'Content-Type': 'application/json' },
        tags: { name: 'CreateUser' },
      }
    );
    
    createUserDuration.add(Date.now() - startTime);
    
    const success = check(response, {
      'create user status is 200': (r) => r.status === 200,
      'create user has id': (r) => JSON.parse(r.body).id !== undefined,
    });
    
    if (success && response.status === 200) {
      createdUsers.push(JSON.parse(response.body).id);
    }
    
    errorRate.add(!success);
  }
  
  // 40% - Get user
  else if (scenario <= 7 && createdUsers.length > 0) {
    const userId = randomItem(createdUsers);
    const startTime = Date.now();
    
    const response = http.get(
      `${BASE_URL}/api/v1/users/${userId}`,
      {
        tags: { name: 'GetUser' },
      }
    );
    
    getUserDuration.add(Date.now() - startTime);
    
    const success = check(response, {
      'get user status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    });
    
    errorRate.add(!success);
  }
  
  // 20% - List users
  else if (scenario <= 9) {
    const page = randomIntBetween(1, 5);
    const pageSize = randomItem([10, 20, 50]);
    const startTime = Date.now();
    
    const response = http.get(
      `${BASE_URL}/api/v1/users?page=${page}&page_size=${pageSize}`,
      {
        tags: { name: 'ListUsers' },
      }
    );
    
    listUsersDuration.add(Date.now() - startTime);
    
    const success = check(response, {
      'list users status is 200': (r) => r.status === 200,
      'list users returns array': (r) => Array.isArray(JSON.parse(r.body)),
    });
    
    errorRate.add(!success);
  }
  
  // 10% - Stream data
  else {
    const size = randomItem([100, 500, 1000]);
    const startTime = Date.now();
    
    const response = http.get(
      `${BASE_URL}/api/v1/stream/large-dataset/${size}`,
      {
        tags: { name: 'StreamData' },
        responseType: 'text',
      }
    );
    
    streamDuration.add(Date.now() - startTime);
    
    const success = check(response, {
      'stream status is 200': (r) => r.status === 200,
      'stream has content': (r) => r.body.length > 0,
    });
    
    errorRate.add(!success);
  }

  sleep(randomIntBetween(1, 3) / 10); // Sleep 0.1-0.3 seconds
}

// Setup function - runs once per VU
export function setup() {
  console.log(`Starting performance test against ${BASE_URL}`);
  
  // Create some initial data
  const setupData = {
    users: [],
    documents: [],
  };
  
  // Create 10 initial users
  for (let i = 0; i < 10; i++) {
    const userData = generateUserData();
    const response = http.post(
      `${BASE_URL}/api/v1/users`,
      JSON.stringify(userData),
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    if (response.status === 200) {
      setupData.users.push(JSON.parse(response.body).id);
    }
  }
  
  return setupData;
}

// Teardown function - runs once after test
export function teardown(data) {
  console.log(`Test complete. Created ${createdUsers.length} users during test.`);
}