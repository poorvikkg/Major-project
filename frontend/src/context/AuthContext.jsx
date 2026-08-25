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
    // Bypassed login for testing without database
    const dummyUser = { 
      id: 1, 
      name: 'Admin (Bypassed)', 
      email: email, 
      role: 'admin', 
      token: 'dummy-token' 
    };
    setUser(dummyUser);
    localStorage.setItem('mpds_user', JSON.stringify(dummyUser));
    return { success: true };
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
