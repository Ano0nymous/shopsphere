import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from '../../api/axios';

export const placeOrder = createAsyncThunk(
  'orders/placeOrder',
  async ({ items, payment_method_id }) => {
    const response = await axios.post('/orders', { items, payment_method_id });
    return response.data;
  }
);

export const fetchOrders = createAsyncThunk('orders/fetchOrders', async () => {
  const response = await axios.get('/orders');
  return response.data;
});

const orderSlice = createSlice({
  name: 'orders',
  initialState: { currentOrder: null, orderHistory: [], status: 'idle', historyStatus: 'idle', error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(placeOrder.pending, (state) => { state.status = 'loading'; state.error = null; })
      .addCase(placeOrder.fulfilled, (state, action) => { state.status = 'succeeded'; state.currentOrder = action.payload; })
      .addCase(placeOrder.rejected, (state, action) => { state.status = 'failed'; state.error = action.error.message; })
      .addCase(fetchOrders.pending, (state) => { state.historyStatus = 'loading'; })
      .addCase(fetchOrders.fulfilled, (state, action) => { state.historyStatus = 'succeeded'; state.orderHistory = action.payload; })
      .addCase(fetchOrders.rejected, (state, action) => { state.historyStatus = 'failed'; state.error = action.error.message; });
  },
});

export default orderSlice.reducer;
