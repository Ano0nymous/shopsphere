import { configureStore } from '@reduxjs/toolkit';
import productReducer from './slices/productSlice';
import authReducer from './slices/authSlice';
import cartReducer from './slices/cartSlice';
import orderReducer from './slices/orderSlice';

export const store = configureStore({
  reducer: {
    products: productReducer,
    auth: authReducer,
    cart: cartReducer,
    orders: orderReducer,
  },
});