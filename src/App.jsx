import React from 'react';
import { AuthProvider } from './hooks/useAuth';
import { ToastProvider } from './components/common/Toast';
import AppRouter from './routes/AppRouter';

/**
 * Root Application component.
 * Integrates global AuthProvider and ToastProvider states.
 * 
 * @returns {JSX.Element}
 */
export const App = () => {
  return (
    <AuthProvider>
      <ToastProvider>
        <AppRouter />
      </ToastProvider>
    </AuthProvider>
  );
};

export default App;
