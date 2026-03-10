// Debug script to check environment variables
console.log('Environment variables:');
console.log('NEXT_PUBLIC_UATP_API_URL:', process.env.NEXT_PUBLIC_UATP_API_URL);
console.log('NEXT_PUBLIC_UATP_API_KEY:', process.env.NEXT_PUBLIC_UATP_API_KEY);
console.log('NODE_ENV:', process.env.NODE_ENV);

// Test what the API client will use
const baseURL = process.env.NEXT_PUBLIC_UATP_API_URL || 'http://localhost:9090';
const apiKey = process.env.NEXT_PUBLIC_UATP_API_KEY || 'dev-key-001';

console.log('API client will use:');
console.log('Base URL:', baseURL);
console.log('API Key:', apiKey);
