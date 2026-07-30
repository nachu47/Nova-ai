import {createContext,useContext,useEffect,useMemo,useState,type ReactNode} from 'react'
type Theme='light'|'dark';type ThemeValue={theme:Theme;toggle:()=>void}
const ThemeContext=createContext<ThemeValue|undefined>(undefined)
export function ThemeProvider({children}:{children:ReactNode}){const [theme,setTheme]=useState<Theme>(()=>(localStorage.getItem('nova_theme') as Theme)||'dark');useEffect(()=>{document.documentElement.classList.toggle('dark',theme==='dark');localStorage.setItem('nova_theme',theme)},[theme]);const value=useMemo(()=>({theme,toggle:()=>setTheme(v=>v==='dark'?'light':'dark')}),[theme]);return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>}
export function useTheme(){const value=useContext(ThemeContext);if(!value)throw new Error('useTheme must be used within ThemeProvider');return value}
