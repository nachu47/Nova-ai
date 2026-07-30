import {createContext,useCallback,useContext,useEffect,useState,type ReactNode} from 'react'
import {api,setTokens} from '@/services/api'
import type {User} from '@/types'
type Registration={organization_name:string;full_name:string;email:string;password:string;timezone:string}
type AuthValue={user:User|null;loading:boolean;login:(email:string,password:string)=>Promise<void>;register:(data:Registration)=>Promise<void>;logout:()=>Promise<void>;reload:()=>Promise<void>}
const AuthContext=createContext<AuthValue|undefined>(undefined)
export function AuthProvider({children}:{children:ReactNode}){
  const[user,setUser]=useState<User|null>(null);const[loading,setLoading]=useState(true)
  const reload=useCallback(async()=>{try{const{data}=await api.get<User>('/auth/me');setUser(data)}catch{setUser(null)}finally{setLoading(false)}},[])
  useEffect(()=>{void reload()},[reload])
  const login=useCallback(async(email:string,password:string)=>{const{data}=await api.post('/auth/login',{email,password});setTokens(data.access_token,data.csrf_token);await reload()},[reload])
  const register=useCallback(async(payload:Registration)=>{const{data}=await api.post('/auth/register',payload);setTokens(data.access_token,data.csrf_token);await reload()},[reload])
  const logout=useCallback(async()=>{try{await api.post('/auth/logout')}finally{setTokens(null,null);setUser(null)}},[])
  return <AuthContext.Provider value={{user,loading,login,register,logout,reload}}>{children}</AuthContext.Provider>
}
export function useAuth(){const value=useContext(AuthContext);if(!value)throw new Error('useAuth must be used within AuthProvider');return value}
