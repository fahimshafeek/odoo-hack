import { describe, expect, it } from 'vitest';
import { routeRedirect } from './guards.js';

describe('AUTH-4 route boundaries', () => {
	it('sends anonymous visitors to login without accepting external return URLs', () => {
		expect(routeRedirect(null, '/app/invoices')).toBe('/login?next=%2Fapp%2Finvoices');
		expect(routeRedirect(null, '//example.com')).toBe('/login');
	});
	it('keeps customers in their portal and staff in their workspace', () => {
		expect(routeRedirect('customer', '/app/invoices')).toBe('/portal/subscriptions');
		expect(routeRedirect('staff', '/portal/invoices')).toBe('/app/dashboard');
		expect(routeRedirect('customer', '/portal/invoices')).toBeNull();
	});
	it('restricts staff management to admins and rejects unknown roles', () => {
		expect(routeRedirect('staff', '/app/staff')).toBe('/app/dashboard');
		expect(routeRedirect('admin', '/app/staff')).toBeNull();
		expect(routeRedirect('owner', '/app/dashboard')).toBe('/login');
	});
});
