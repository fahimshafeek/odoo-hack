import { api } from '#lib/auth/session.js';

/** Fetch an authorized PDF through the shared API client (INV-3).
 * @param {string} path */
export async function openPdf(path) {
	const popup = window.open('about:blank', '_blank');
	if (popup) {
		popup.opener = null;
		popup.document.body.textContent = 'Preparing your document…';
	}
	try {
		// PDF paths are supplied by feature routes; the middleware still handles auth/errors.
		const binaryClient = /** @type {import('openapi-fetch').Client<Record<string, any>>} */ (api);
		const { data } = await binaryClient.GET(path, { parseAs: 'blob' });
		if (!(data instanceof Blob)) throw new Error('We could not prepare this document.');
		const url = URL.createObjectURL(data);
		if (popup) popup.location.href = url;
		else {
			const link = document.createElement('a');
			link.href = url;
			link.download = 'invoice.pdf';
			link.click();
		}
		setTimeout(() => URL.revokeObjectURL(url), 60000);
	} catch (error) {
		popup?.close();
		throw error;
	}
}
