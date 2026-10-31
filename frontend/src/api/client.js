import createClient from 'openapi-fetch';
import { ApiError } from './errors.js';

/** @type {typeof fetch | undefined} */
let transport;

/** Install an explicit transport during development preview initialization. @param {typeof fetch | undefined} next */
export function setApiTransport(next) {
	transport = next;
}

/**
 * Build the A6 client with per-session credentials and normalized errors.
 * @param {{getToken: () => string | null, onUnauthorized: () => void, fetcher?: typeof fetch}} options
 */
export function createApiClient({
	getToken,
	onUnauthorized,
	fetcher = (input, init) => (transport ?? fetch)(input, init)
}) {
	/** @type {import('openapi-fetch').Client<import('./schema').paths>} */
	const client = createClient({
		baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
		fetch: fetcher
	});
	client.use({
		onRequest({ request }) {
			const token = getToken();
			if (token) request.headers.set('Authorization', `Bearer ${token}`);
			return request;
		},
		async onResponse({ response, request }) {
			if (response.ok) return response;
			if (response.status === 401 && !new URL(request.url).pathname.endsWith('/auth/login')) {
				onUnauthorized();
			}
			throw new ApiError(
				response.status,
				await response
					.clone()
					.json()
					.catch(() => null)
			);
		}
	});
	return client;
}
