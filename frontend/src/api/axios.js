import axios from 'axios';

// Every backend route lives under /api (ingress strips the prefix).
const axiosInstance = axios.create({ baseURL: '/api' });

axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Surface the backend's error message instead of axios' generic "Request failed with status 4xx".
axiosInstance.interceptors.response.use(
  (res) => res,
  (error) => {
    const msg = error.response?.data?.error;
    if (msg) error.message = msg;
    if (error.response?.status === 401 && localStorage.getItem('token')) {
      localStorage.removeItem('token'); // expired/invalid token: drop it so the UI shows logged-out state
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
