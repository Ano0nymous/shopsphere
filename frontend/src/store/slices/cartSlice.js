import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from '../../api/axios';

export const fetchCart = createAsyncThunk('cart/fetchCart', async () => (await axios.get('/cart')).data);

export const addToCart = createAsyncThunk('cart/addToCart', async ({ product_id, quantity = 1 }, { dispatch }) => {
  const response = await axios.post('/cart', { product_id, quantity });
  dispatch(fetchCart()); // keep the navbar badge in sync
  return response.data;
});

export const removeFromCart = createAsyncThunk('cart/removeFromCart', async (product_id) => {
  await axios.delete('/cart', { data: { product_id } });
  return product_id;
});

export const clearCart = createAsyncThunk('cart/clearCart', async () => { await axios.delete('/cart'); });

const cartSlice = createSlice({
  name: 'cart',
  initialState: { items: [], status: 'idle', error: null },
  reducers: {
    resetCart: (state) => { state.items = []; state.status = 'idle'; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCart.pending, (state) => { state.status = 'loading'; })
      .addCase(fetchCart.fulfilled, (state, action) => { state.status = 'succeeded'; state.items = action.payload; })
      .addCase(fetchCart.rejected, (state, action) => { state.status = 'failed'; state.error = action.error.message; })
      .addCase(removeFromCart.fulfilled, (state, action) => {
        state.items = state.items.filter((item) => item.product_id !== action.payload);
      })
      .addCase(clearCart.fulfilled, (state) => { state.items = []; });
  },
});

export const { resetCart } = cartSlice.actions;
export default cartSlice.reducer;
