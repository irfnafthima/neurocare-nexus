import React, { createContext, useContext, useState, useEffect } from 'react';

/**
 * @typedef {Object} User
 * @property {string} name - The user's full name.
 * @property {string} email - The user's email address.
 * @property {string} phone - The user's phone number.
 * @property {string} role - The user's role (patient, doctor, caregiver, family, admin).
 * @property {string} [npi] - NPI / license number (for doctors).
 * @property {string} [deviceId] - Device Serial Number (for patients).
 * @property {string} [agencyId] - Caregiver agency ID (for caregivers).
 * @property {string} [patientId] - Authorized patient access ID (for family members).
 * @property {string} [accessKey] - System Access Key (for administrators).
 */

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('nexus_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('nexus_user');
      }
    }
    setIsLoading(false);
  }, []);

  /**
   * Connects to backend REST API to validate credentials and log in.
   */
  const login = async (email, password, role, credentials = {}) => {
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:5000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role, credentials })
      });

      if (!res.ok) {
        const errMsg = await res.text();
        throw new Error(errMsg);
      }

      const authenticatedUser = await res.json();
      setUser(authenticatedUser);
      localStorage.setItem('nexus_user', JSON.stringify(authenticatedUser));
      setIsLoading(false);
      return true;
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  /**
   * Connects to backend REST API to register a new user account.
   */
  const register = async (userData) => {
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:5000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fullName: userData.fullName,
          email: userData.email,
          phone: userData.phone || '',
          role: userData.role,
          npi: userData.npi || '',
          deviceId: userData.deviceId || '',
          agencyId: userData.agencyId || '',
          patientId: userData.patientId || '',
          accessKey: userData.accessKey || ''
        })
      });

      if (!res.ok) {
        const errMsg = await res.text();
        throw new Error(errMsg);
      }

      const newUser = await res.json();
      if (newUser.approved === false) {
        setIsLoading(false);
        return { isPendingApproval: true, message: newUser.message };
      }
      setUser(newUser);
      localStorage.setItem('nexus_user', JSON.stringify(newUser));
      setIsLoading(false);
      return { isPendingApproval: false };
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('nexus_user');
  };

  /**
   * Helper to perform fetch requests with JWT authorization header automatically attached.
   */
  const authFetch = async (url, options = {}) => {
    let token = user?.token;
    if (!token) {
      const storedUser = localStorage.getItem('nexus_user');
      if (storedUser) {
        try {
          token = JSON.parse(storedUser)?.token;
        } catch (e) {}
      }
    }
    const headers = {
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return fetch(url, { ...options, headers });
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    authFetch
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
