"use client";

import { useState } from "react";

import { NavProvider } from "@/context/NavContext";
import { ThemeProvider } from "@/context/ThemeContext";

import { DashboardHeader } from "./components/DashboardHeader";
import { AppSidebar } from "./components/AppSidebar";

export function DashboardShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <ThemeProvider>
      <NavProvider>
        <div className="flex min-h-screen bg-slate-50">

         

          <div className="flex-1">

            

            <main>
              {children}
            </main>

          </div>

        </div>
      </NavProvider>
    </ThemeProvider>
  );
}