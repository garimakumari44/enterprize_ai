'use client'

import { AuthProvider, useAuth } from "../../../context/AuthContext";
import { ThemeProvider } from "../../../context/ThemeContext";
import { NavProvider } from "../../../context/NavContext";
import { AuthLanding } from "../../../components/AuthLanding";
import { Dashboard } from "../components/Dashboard";

function Gate() {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-cyan-500" />
          <p className="text-sm text-slate-400">
            Loading workspace…
          </p>
        </div>
      </div>
    );
  }

  return session ? (
    <NavProvider>
      <Dashboard />
    </NavProvider>
  ) : (
    <AuthLanding />
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Gate />
      </ThemeProvider>
    </AuthProvider>
  );
}

