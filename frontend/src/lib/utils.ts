import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const initials = (name?: string | null): string => {
  const words = (name ?? '').replace(/\([^)]*\)/g, ' ').split(/\s+/).filter(word => /^\p{L}/u.test(word))
  return words.slice(0, 2).map(word => word[0].toUpperCase()).join('') || '??'
}
