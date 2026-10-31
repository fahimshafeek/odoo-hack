import { z } from 'zod';

/** AUTH-2 password checklist shared with the registration UI. @param {string} password */
export function passwordChecks(password) {
	return {
		length: password.length >= 9 && password.length <= 128,
		uppercase: /[A-Z]/.test(password),
		lowercase: /[a-z]/.test(password),
		special: /[^A-Za-z0-9]/.test(password)
	};
}

export const emailSchema = z
	.string()
	.trim()
	.toLowerCase()
	.max(254)
	.email('Enter a valid email address.');
export const passwordSchema = z
	.string()
	.min(9, 'Use at least 9 characters.')
	.max(128)
	.regex(/[A-Z]/, 'Add an uppercase letter.')
	.regex(/[a-z]/, 'Add a lowercase letter.')
	.regex(/[^A-Za-z0-9]/, 'Add a special character.');
export const personNameSchema = z.string().trim().min(1, 'Enter a name.').max(120);
/** Length-limited free text (plan 9.8). @param {number} [max] */
export const notesSchema = (max = 2000) => z.string().trim().max(max);
export const phoneSchema = z
	.string()
	.trim()
	.regex(/^[+\d ]*$/, 'Use digits, spaces, or + only.')
	.refine((value) => {
		const digits = value.replace(/\D/g, '').length;
		return digits >= 7 && digits <= 15;
	}, 'Use 7–15 digits.');
export const moneySchema = z
	.union([z.string(), z.number().finite()])
	.transform(String)
	.refine(
		(value) => /^\d{1,10}(?:\.\d{1,2})?$/.test(value),
		'Enter a positive amount with up to 2 decimal places.'
	)
	.transform((value) => {
		const [whole, fraction = ''] = value.split('.');
		return `${whole}.${fraction.padEnd(2, '0')}`;
	});
/** Enforce the plan's minimum quantity without doing pricing arithmetic. @param {number} [minimum] */
export const quantitySchema = (minimum = 1) =>
	z.coerce.number().int('Enter a whole number.').min(Math.max(1, minimum));
export const uuidSchema = z.string().uuid('Select a valid record.');
export const dateSchema = z
	.string()
	.regex(/^\d{4}-\d{2}-\d{2}$/, 'Choose a date.')
	.refine((value) => {
		const parsed = new Date(`${value}T00:00:00Z`);
		return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
	}, 'Choose a valid date.');
export const percentSchema = z.coerce.number().min(0).max(100).multipleOf(0.01);
