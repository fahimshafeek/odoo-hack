import { describe, expect, it, vi } from 'vitest';
import { createApiClient } from './client.js';

describe('A6 API boundary', () => {
	it('injects the current bearer token into requests', async () => {
		const fetcher = vi.fn(async (request) => {
			expect(request.headers.get('Authorization')).toBe('Bearer session-token');
			return Response.json({ id: 'user-id' });
		});
		const client = createApiClient({
			getToken: () => 'session-token',
			onUnauthorized: vi.fn(),
			fetcher
		});
		await client.GET('/auth/me');
		expect(fetcher).toHaveBeenCalledOnce();
	});
	it('expires a rejected session and returns the canonical error envelope', async () => {
		const onUnauthorized = vi.fn();
		const client = createApiClient({
			getToken: () => 'expired',
			onUnauthorized,
			fetcher: async () =>
				Response.json(
					{ error: { code: 'unauthorized', message: 'Session expired.' } },
					{ status: 401 }
				)
		});
		await expect(client.GET('/auth/me')).rejects.toMatchObject({
			status: 401,
			code: 'unauthorized'
		});
		expect(onUnauthorized).toHaveBeenCalledOnce();
	});
	it('does not expire a session for a failed login', async () => {
		const onUnauthorized = vi.fn();
		const client = createApiClient({
			getToken: () => null,
			onUnauthorized,
			fetcher: async () => new Response(null, { status: 401 })
		});
		await expect(
			client.POST('/auth/login', { body: { email: 'person@example.com', password: 'invalid' } })
		).rejects.toMatchObject({ status: 401 });
		expect(onUnauthorized).not.toHaveBeenCalled();
	});
	it('keeps internal failure details out of user messages', async () => {
		const client = createApiClient({
			getToken: () => null,
			onUnauthorized: vi.fn(),
			fetcher: async () =>
				Response.json({ error: { message: 'private database details' } }, { status: 500 })
		});
		await expect(client.GET('/auth/me')).rejects.toMatchObject({
			message: 'The server could not complete your request.'
		});
	});
});
