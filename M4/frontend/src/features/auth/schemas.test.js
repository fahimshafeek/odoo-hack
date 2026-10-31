import { describe, it, expect } from 'vitest';
import { authSchema, authDestination } from './schemas.js';

describe('account form validation', () => {
	it('requires matching passwords and the shared M1 password rules', () => {
		const schema = authSchema('signup');
		const values = {
			full_name: 'Account holder',
			email: 'person@example.com',
			password: 'StrongPassword!',
			confirm_password: 'StrongPassword!',
			company_name: '',
			phone: ''
		};
		expect(schema.safeParse(values).success).toBe(true);
		expect(schema.safeParse({ ...values, confirm_password: 'DifferentPassword!' }).success).toBe(
			false
		);
		expect(
			schema.safeParse({ ...values, password: 'short', confirm_password: 'short' }).success
		).toBe(false);
		expect(
			schema.safeParse({
				...values,
				email: 'person@example.com',
				password: 'person@example.com',
				confirm_password: 'person@example.com'
			}).success
		).toBe(false);
	});
	it('requires a reset token and matching new passwords', () => {
		const values = {
			token: 'single-use-token',
			new_password: 'NewPassword!',
			confirm_password: 'NewPassword!'
		};
		expect(authSchema('reset').safeParse(values).success).toBe(true);
		expect(authSchema('reset').safeParse({ ...values, token: '' }).success).toBe(false);
		expect(
			authSchema('reset').safeParse({ ...values, confirm_password: 'OtherPassword!' }).success
		).toBe(false);
	});
	it('allows existing passwords at login without imposing registration requirements', () => {
		expect(
			authSchema('login').safeParse({ email: 'person@example.com', password: 'existing-password' })
				.success
		).toBe(true);
		expect(
			authSchema('login').safeParse({ email: 'person@example.com', password: '' }).success
		).toBe(false);
	});
	it('restricts return URLs to the authenticated role and rejects external or traversed destinations', () => {
		expect(authDestination('staff', '/app/invoices?payment_filter=overdue')).toEqual({
			path: 'app/invoices',
			search: '?payment_filter=overdue'
		});
		for (const next of [
			'https://example.com/app/dashboard',
			'//example.com/app/dashboard',
			'/app/../../login',
			'/app/dashboard'
		])
			expect(authDestination('customer', next)).toEqual({
				path: 'portal/subscriptions',
				search: ''
			});
		expect(authDestination('staff', '/portal/profile')).toEqual({
			path: 'app/dashboard',
			search: ''
		});
	});
});
