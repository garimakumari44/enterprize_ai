"use client"
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { Session, User, } from "../types/auth";

import {
  login,
  register,
  logout,
  getCurrentUser,
} from "../lib/auth"


type AuthResult = {
  error: string | null;
};


type AuthContextValue = {
  user: User | null;
  session: Session | null;
  loading: boolean;

  signUp: (
    fullName: string,
    email: string,
    password: string
  ) => Promise<AuthResult>;

  signIn: (
    email: string,
    password: string
  ) => Promise<AuthResult>;

  signOut: () => Promise<void>;
};


const AuthContext =
  createContext<AuthContextValue | undefined>(undefined);



export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {

  const [session, setSession] =
    useState<Session | null>(null);

  const [loading, setLoading] =
    useState(true);



  // Restore session when app starts
  useEffect(() => {

    async function initialize() {

      try {

        const accessToken =
          localStorage.getItem("accessToken");


        if (!accessToken) {
          setLoading(false);
          return;
        }


        const user =
          await getCurrentUser();


        setSession({
          accessToken,
          user,
        });


      } catch (error) {

        localStorage.removeItem(
          "accessToken"
        );

        setSession(null);

      } finally {

        setLoading(false);

      }

    }


    initialize();

  }, []);





  const value = useMemo<AuthContextValue>(
    () => ({


      user:
        session?.user ?? null,


      session,


      loading,



      // ============================
      // REGISTER
      // ============================

      async signUp(
        fullName,
        email,
        password
      ) {

        try {


          await register(
           
            fullName,
            email,
            password
          );


          return {
            error: null,
          };


        } catch (err: any) {


          return {
            error:
              err.response?.data?.detail ??
              err.message ??
              "Registration failed",
          };

        }

      },





      // ============================
      // LOGIN
      // ============================

      async signIn(
        email,
        password
      ) {


        try {


          const token =
            await login(
              email,
              password
            );



          /*
             Backend returns:

             {
                access_token,
                refresh_token,
                token_type
             }

          */


          localStorage.setItem(
            "accessToken",
            token.access_token
          );



          const user =
            await getCurrentUser();



          const newSession = {

            accessToken:
              token.access_token,


            


            user,

          };



          setSession(
            newSession
          );



          return {
            error:null,
          };



        } catch(err:any) {


          localStorage.removeItem(
            "accessToken"
          );


          return {

            error:
              err.response?.data?.detail ??
              err.message ??
              "Login failed",

          };

        }

      },





      // ============================
      // LOGOUT
      // ============================

      async signOut() {


        try {

          await logout();

        } finally {


          localStorage.removeItem(
            "accessToken"
          );


          setSession(null);

        }

      },


    }),

    [session, loading]

  );





  return (

    <AuthContext.Provider value={value}>

      {children}

    </AuthContext.Provider>

  );

}





export function useAuth() {

  const context =
    useContext(AuthContext);


  if (!context) {

    throw new Error(
      "useAuth must be used within AuthProvider"
    );

  }


  return context;

}