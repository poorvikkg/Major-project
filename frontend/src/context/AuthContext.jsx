import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('mpds_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      
      if (response.ok && data.status === 'success') {
        const userData = { ...data.data.user, token: data.data.access_token };
        setUser(userData);
        localStorage.setItem('mpds_user', JSON.stringify(userData));
        return { success: true };
      } else {
        return { success: false, message: data.message || 'Login failed' };
      }
    } catch (err) {
      return { success: false, message: 'Network error. Please try again later.' };
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('mpds_user');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
