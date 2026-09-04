import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from '../../api/axios';

// Helper functions
const saveToken = (token) => localStorage.setItem('token', token);
const getToken = () => localStorage.getItem('token');

// Decode JWT to get username (no library needed)
const decodeToken = (token) => {
  try {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload));
    return decoded.username || 'User';
  } catch {
    return 'User';
  }
};

export const signup = createAsyncThunk(
  'auth/signup',
  async ({ username, password }) => {
    const response = await axios.post('/signup', { username, password });
    return response.data;
  }
);

export const login = createAsyncThunk(
  'auth/login',
  async ({ username, password }) => {
    const response = await axios.post('/login', { username, password });
    const { token } = response.data;
    saveToken(token);                // <-- save to localStorage immediately
    return { token, username };      // <-- forward username explicitly
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    token: getToken(),
    username: getToken() ? decodeToken(getToken()) : null,
    status: 'idle',
    error: null,
  },
  reducers: {
    logout: (state) => {
      state.token = null;
      state.username = null;
      localStorage.removeItem('token');
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(signup.fulfilled, (state) => {
        state.error = null;
      })
      .addCase(login.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.token = action.payload.token;
        state.username = action.payload.username;
      })
      .addCase(login.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;