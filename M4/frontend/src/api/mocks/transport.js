import { getResponse } from 'msw';
import { handlers } from './handlers.js';

/** Serve explicitly enabled preview requests locally; never fall through to an offline backend.
 * @param {Parameters<typeof fetch>[0]} input
 * @param {RequestInit} [init]
 * @returns {Promise<Response>} */
export async function previewFetch(input, init) {
	const request = new Request(input, init);
	request.signal.throwIfAborted();
	const response = await getResponse(handlers, request);
	request.signal.throwIfAborted();
	return (
		response ??
		Response.json(
			{
				error: {
					code: 'not_found',
					message: 'This endpoint is not available in the frontend preview.',
					fields: {}
				}
			},
			{ status: 404 }
		)
	);
}
