import { afterEach, expect, it, vi } from 'vitest';
import { createApiClient, setApiTransport } from '../client.js';
import { previewFetch } from './transport.js';

afterEach(() => {
	setApiTransport(undefined);
	vi.unstubAllGlobals();
});

it('serves clients created before preview initialization without accessing the backend', async () => {
	const network = vi.fn(() => Promise.reject(new TypeError('Failed to fetch')));
	vi.stubGlobal('fetch', network);
	const client = /** @type {any} */ (
		createApiClient({ getToken: () => 'preview-admin', onUnauthorized: vi.fn() })
	);
	setApiTransport(previewFetch);
	for (const path of [
		'/subscriptions',
		'/customers',
		'/products',
		'/plans',
		'/taxes',
		'/discounts',
		'/staff',
		'/reports/summary',
		'/reports/revenue-by-month',
		'/reports/overdue-invoices',
		'/auth/me',
		'/payments',
		'/billing/runs',
		'/payment-terms',
		'/quotation-templates',
		'/me/subscriptions',
		'/me/invoices',
		'/me/payments',
		'/me/profile'
	]) {
		const { data, response } = await client.GET(path);
		expect(response.status).toBe(200);
		expect(data).toBeTruthy();
	}
	expect(network).not.toHaveBeenCalled();
});

it('keeps role switching and preview resets local', async () => {
	const login = await previewFetch(
		new Request('http://localhost:8000/auth/login', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email: 'customer@preview.brightloop.test' })
		})
	);
	expect((await login.json()).user.role).toBe('customer');
	const reset = await previewFetch(
		new Request('http://localhost:8000/__preview/reset', { method: 'POST' })
	);
	expect(reset.ok).toBe(true);
});
