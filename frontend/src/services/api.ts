import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'
export const api = axios.create({ baseURL: API_BASE, withCredentials: true, headers: { 'Content-Type': 'application/json' } })
let accessToken=localStorage.getItem('nova_access_token')
let csrfToken=localStorage.getItem('nova_csrf_token')
let refreshPromise:Promise<string>|null=null
export function setTokens(access:string|null,csrf:string|null){accessToken=access;csrfToken=csrf;if(access)localStorage.setItem('nova_access_token',access);else localStorage.removeItem('nova_access_token');if(csrf)localStorage.setItem('nova_csrf_token',csrf);else localStorage.removeItem('nova_csrf_token')}
api.interceptors.request.use((config:InternalAxiosRequestConfig)=>{if(accessToken)config.headers.Authorization=`Bearer ${accessToken}`;return config})
api.interceptors.response.use(r=>r,async(error:AxiosError)=>{const original=error.config as (InternalAxiosRequestConfig&{_retry?:boolean})|undefined;if(error.response?.status===401&&original&&!original._retry&&!original.url?.includes('/auth/')){original._retry=true;refreshPromise??=api.post('/auth/refresh',{}, {headers:{'X-CSRF-Token':csrfToken??''}}).then(({data})=>{setTokens(data.access_token,data.csrf_token);return data.access_token}).finally(()=>{refreshPromise=null});try{const token=await refreshPromise;original.headers.Authorization=`Bearer ${token}`;return api(original)}catch{setTokens(null,null);window.location.assign('/login')}}return Promise.reject(error)})
export function errorMessage(error:unknown){if(axios.isAxiosError(error)){const body=error.response?.data as {detail?:unknown}|undefined;const detail=body?.detail;return typeof detail==='string'?detail:'The request could not be completed.'}return error instanceof Error?error.message:'Unexpected error'}
