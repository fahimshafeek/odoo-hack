import { z } from 'zod';
import {
	emailSchema,
	passwordSchema,
	personNameSchema,
	notesSchema,
	phoneSchema
} from '#lib/validators.js';

/** AUTH-1/2/3 form validation follows M1's public request schemas. @param {string} mode */
export function authSchema(mode) {
	if (mode === 'signup')
		return z
			.object({
				role: z.enum(['customer', 'staff', 'admin']).default('customer'),
				email: emailSchema,
				full_name: personNameSchema,
				password: passwordSchema,
				confirm_password: z.string(),
				company_name: notesSchema(120),
				phone: z.union([z.literal(''), phoneSchema])
			})
			.superRefine((values, ctx) => {
				if (values.password !== values.confirm_password)
					ctx.addIssue({
						code: 'custom',
						path: ['confirm_password'],
						message: 'Passwords do not match.'
					});
				if (values.password.trim().toLowerCase() === values.email)
					ctx.addIssue({
						code: 'custom',
						path: ['password'],
						message: 'Password cannot be the same as your email.'
					});
			});
	if (mode === 'forgot') return z.object({ email: emailSchema });
	if (mode === 'reset')
		return z
			.object({
				token: z.string().min(1),
				new_password: passwordSchema,
				confirm_password: z.string()
			})
			.refine((values) => values.new_password === values.confirm_password, {
				path: ['confirm_password'],
				message: 'Passwords do not match.'
			});
	return z.object({ email: emailSchema, password: z.string().min(1, 'Enter your password.') });
}

/** Constrain AUTH-4 return destinations to the signed-in role's local workspace. @param {string} role @param {string|null} next */
export function authDestination(role, next) {
	const fallback = role === 'customer' ? '/portal/subscriptions' : '/app/dashboard';
	try {
		const url = new URL(next || fallback, 'https://local.invalid');
		const prefix = role === 'customer' ? '/portal/' : '/app/';
		if (url.origin === 'https://local.invalid' && url.pathname.startsWith(prefix))
			return { path: url.pathname.slice(1), search: url.search };
	} catch {
		/* Use the role's landing page for malformed URLs. */
	}
	return { path: fallback.slice(1), search: '' };
}
