"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { AuthProvider, useAuth } from "../context/AuthContext";
import { AuthLanding } from "../components/AuthLanding";

function LandingGate() {
  const { session, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && session) {
      router.replace("/dashboard");
    }
  }, [loading, session, router]);

  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-cyan-500" />

          <p className="text-sm text-slate-500">
            Loading workspace...
          </p>
        </div>
      </div>
    );
  }

  if (session) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50 dark:bg-slate-950">
        <p className="text-sm text-slate-500">
          Redirecting to dashboard...
        </p>
      </div>
    );
  }

  return <AuthLanding />;
}

export default function HomePage() {
  return (
    <AuthProvider>
      <LandingGate />
    </AuthProvider>
  );
}