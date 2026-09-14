"use client"

import { useState, type FormEvent } from 'react';
import { Loader2, Mail, Lock, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

type Mode = 'signin' | 'signup';

export function AuthForm() {
  const { signIn, signUp } = useAuth();

  const [mode, setMode] = useState<Mode>('signin');

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [showPwd, setShowPwd] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);


  const switchMode = (next: Mode) => {
    setMode(next);
    setError(null);
    setInfo(null);

    if (next === 'signin') {
      setFullName('');
    }
  };


  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();

    setError(null);
    setInfo(null);


    if (mode === 'signup' && fullName.trim().length < 2) {
      setError('Full name must be at least 2 characters.');
      return;
    }


    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }


    setSubmitting(true);


    const result =
      mode === 'signin'
        ? await signIn(email.trim(), password)
        : await signUp(
            fullName.trim(),
            email.trim(),
            password
          );


    setSubmitting(false);


    if (result.error) {
      setError(result.error);
      return;
    }


    if (mode === 'signup') {
      setInfo('Account created. You can sign in now.');

      setMode('signin');

      setFullName('');
      setEmail('');
      setPassword('');
    }
  };


  return (
    <div className="flex h-full flex-col justify-center px-6 py-10 sm:px-10 lg:px-16">

      <div className="mx-auto w-full max-w-sm">

        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
            {mode === 'signin'
              ? 'Welcome back'
              : 'Create your account'}
          </h1>

          <p className="mt-1.5 text-sm text-slate-500">
            {mode === 'signin'
              ? 'Sign in to your orchestration workspace.'
              : 'Start orchestrating intelligent document workflows.'}
          </p>
        </div>



        <div className="mb-6 grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1">

          <button
            type="button"
            onClick={() => switchMode('signin')}
            className={`rounded-lg py-2 text-sm font-medium transition-all ${
              mode === 'signin'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            Sign in
          </button>


          <button
            type="button"
            onClick={() => switchMode('signup')}
            className={`rounded-lg py-2 text-sm font-medium transition-all ${
              mode === 'signup'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            Register
          </button>

        </div>




        <form onSubmit={onSubmit} className="space-y-4" noValidate>


          {mode === 'signup' && (
            <div>

              <label
                htmlFor="full_name"
                className="mb-1.5 block text-xs font-medium text-slate-600"
              >
                Full name
              </label>


              <input
                id="full_name"
                type="text"
                autoComplete="name"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your full name"
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition-all focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20"
              />

            </div>
          )}






          <div>

            <label
              htmlFor="email"
              className="mb-1.5 block text-xs font-medium text-slate-600"
            >
              Work email
            </label>


            <div className="group relative">

              <Mail
                size={16}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />


              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e)=>setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-10 pr-3 text-sm text-slate-900 placeholder:text-slate-400"
              />

            </div>

          </div>






          <div>


            <label
              htmlFor="password"
              className="mb-1.5 block text-xs font-medium text-slate-600"
            >
              Password
            </label>


            <div className="group relative">


              <Lock
                size={16}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />


              <input
                id="password"
                type={showPwd ? 'text' : 'password'}
                autoComplete={
                  mode === 'signin'
                    ? 'current-password'
                    : 'new-password'
                }
                required
                value={password}
                onChange={(e)=>setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-10 pr-16 text-sm text-slate-900"
              />


              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs"
              >
                {showPwd ? 'Hide' : 'Show'}
              </button>


            </div>

          </div>






          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-700">

              <AlertCircle size={16}/>

              <span>
                {error}
              </span>

            </div>
          )}




          {info && (
            <div className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-sm text-emerald-700">

              <CheckCircle2 size={16}/>

              <span>
                {info}
              </span>

            </div>
          )}






          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 py-2.5 text-sm font-semibold text-white disabled:opacity-70"
          >

            {submitting ? (
              <>
                <Loader2 size={16} className="animate-spin"/>
                Creating...
              </>
            ) : (
              <>
                {mode === 'signin'
                  ? 'Sign in'
                  : 'Create account'}

                <ArrowRight size={16}/>
              </>
            )}

          </button>


        </form>


      </div>

    </div>
  );
}