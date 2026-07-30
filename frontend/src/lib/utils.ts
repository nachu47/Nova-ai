import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
export function money(value: number, currency = 'GBP') { return new Intl.NumberFormat('en-GB', { style: 'currency', currency }).format(value) }
export function duration(seconds: number) { const m=Math.floor(seconds/60); const s=seconds%60; return `${m}:${String(s).padStart(2,'0')}` }
