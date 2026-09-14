import { Logo } from './Logo';
import { BrandStage } from './BrandStage';
import { AuthForm } from './AuthForm';

export function AuthLanding() {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[1.05fr_1fr]">
      {/* Brand stage */}
      <div className="relative hidden lg:block">
        <BrandStage />
        <div className="absolute left-10 top-10 lg:left-14 lg:top-14">
          <Logo variant="light" size="lg" />
        </div>
      </div>

      {/* Form panel */}
      <div className="relative flex flex-col bg-white">
        {/* Mobile logo */}
        <div className="flex items-center justify-between px-6 pt-6 sm:px-10 lg:hidden">
          <Logo variant="dark" size="md" />
        </div>
        {/* Desktop top-right logo */}
        <div className="absolute right-10 top-10 hidden lg:block">
          {/* <Logo variant="dark" size="md" /> */}
        </div>

        <div className="flex-1">
          <AuthForm />
        </div>

        <footer className="px-6 pb-6 text-center text-[11px] text-slate-400 sm:px-10">
          © {new Date().getFullYear()} DocumentIQ — Enterprise Document Intelligence Platform
        </footer>
      </div>
    </div>
  );
}
