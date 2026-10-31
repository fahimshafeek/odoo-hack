/** Normalize the A3 error envelope without displaying internal server failures. */
export class ApiError extends Error {
	/** @param {number} status @param {any} body */
	constructor(status, body) {
		const error = body?.error;
		const message =
			status >= 500
				? 'The server could not complete your request.'
				: error?.message || 'We could not complete your request. Please try again.';
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.code = error?.code || 'request_failed';
		this.fields = error?.fields || {};
	}
}
