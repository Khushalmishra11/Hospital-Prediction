import React, { createContext, useContext, useState, useEffect } from "react";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from "firebase/auth";
import { auth } from "../firebase";
import { authAPI } from "../api";

const AuthContext = createContext();

function normalizeAuthError(err) {
  const code = err?.code || "";
  if (code === "auth/email-already-in-use") {
    return "This email is already registered. Please login instead.";
  }
  if (code === "auth/invalid-credential") {
    return "Invalid email or password.";
  }
  if (code === "auth/wrong-password") {
    return "Incorrect password. Please try again.";
  }
  if (code === "auth/too-many-requests") {
    return "Too many attempts. Please wait a minute and try again.";
  }
  return err?.response?.data?.detail || err?.message || "Authentication failed";
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const register = async (email, password, fullName) => {
    setError("");
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      
      // Register user in backend
      await authAPI.register(email, password, fullName);
      
      // Get ID token for backend
      const token = await userCredential.user.getIdToken();
      localStorage.setItem("firebaseToken", token);
      
      return userCredential.user;
    } catch (err) {
      // If user already exists, try logging in with the same credentials,
      // then upsert the profile in backend.
      if (err?.code === "auth/email-already-in-use") {
        try {
          const userCredential = await signInWithEmailAndPassword(auth, email, password);
          await authAPI.register(email, password, fullName);
          const token = await userCredential.user.getIdToken();
          localStorage.setItem("firebaseToken", token);
          return userCredential.user;
        } catch (loginErr) {
          const message =
            loginErr?.code === "auth/invalid-credential"
              ? "Email already exists. Please use Login, or use Forgot Password in Firebase console flow."
              : normalizeAuthError(loginErr);
          setError(message);
          throw new Error(message);
        }
      }

      const message = normalizeAuthError(err);
      setError(message);
      throw new Error(message);
    }
  };

  const login = async (email, password) => {
    setError("");
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      
      // Get ID token for backend
      const token = await userCredential.user.getIdToken();
      localStorage.setItem("firebaseToken", token);
      
      return userCredential.user;
    } catch (err) {
      const message = normalizeAuthError(err);
      setError(message);
      throw new Error(message);
    }
  };

  const logout = async () => {
    setError("");
    try {
      await signOut(auth);
      localStorage.removeItem("firebaseToken");
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      if (user) {
        try {
          const token = await user.getIdToken();
          localStorage.setItem("firebaseToken", token);
        } catch (err) {
          console.error("Error getting token:", err);
        }
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const value = {
    currentUser,
    register,
    login,
    logout,
    loading,
    error,
    setError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
