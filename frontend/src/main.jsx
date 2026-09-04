import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import { store } from './store/store';
import App from './App';

// Publishable key only (pk_...). Set VITE_STRIPE_PUBLISHABLE_KEY at build time.
const stripePromise = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY
  ? loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY)
  : null;

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Provider store={store}>
      <MantineProvider
        defaultColorScheme="dark"
        theme={{
          components: {
            Button: { defaultProps: { radius: 'md' } },
            Card: { defaultProps: { radius: 'lg' } },
          },
          colors: {
            brand: ['#e6f7ff', '#bae7ff', '#91d5ff', '#69c0ff', '#40a9ff',
              '#1890ff', '#096dd9', '#0050b3', '#003a8c', '#002766'],
          },
          primaryColor: 'brand',
          fontFamily: 'Inter, sans-serif',
          headings: { fontFamily: 'Inter, sans-serif' },
        }}
      >
        <Notifications position="top-right" />
        <Elements stripe={stripePromise}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </Elements>
      </MantineProvider>
    </Provider>
  </React.StrictMode>
);
