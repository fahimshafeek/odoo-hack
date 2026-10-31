import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge layout and variant classes. @param {...import('clsx').ClassValue} inputs */
export function cn(...inputs) {
	return twMerge(clsx(inputs));
}
