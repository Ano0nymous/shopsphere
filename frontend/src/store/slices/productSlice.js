import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from '../../api/axios';


// Fetch all products
export const fetchProducts = createAsyncThunk(
  'products/fetchProducts',
  async () => {
    const response = await axios.get(`/products`);
    return response.data;
  }
);

// Add a new product (admin)
export const addProduct = createAsyncThunk(
  'products/addProduct',
  async ({ name, price }) => {
    const response = await axios.post(`/products`, { name, price });
    return response.data;  // the created product object
  }
);

const productSlice = createSlice({
  name: 'products',
  initialState: {
    items: [],
    status: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      // fetchProducts
      .addCase(fetchProducts.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      // addProduct
      .addCase(addProduct.fulfilled, (state, action) => {
        // Add the newly created product to the list without refetching
        state.items.push(action.payload);
      });
  },
});

export default productSlice.reducer;