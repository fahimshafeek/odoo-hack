import { setupWorker } from 'msw/browser';
import { asset } from '$app/paths';
import { auth } from '#lib/auth/session.js';
import { handlers } from './handlers.js';
import { previewSession } from './store.js';

/** Start only from the DEV + VITE_USE_MOCKS guarded client hook. */
export async function startPreview() {
	const worker = setupWorker(...handlers);
	await worker.start({
		serviceWorker: { url: asset('mockServiceWorker.js') },
		onUnhandledRequest: 'bypass',
		quiet: true
	});
	auth.setSession(previewSession(location.pathname.startsWith('/portal') ? 'customer' : 'admin'));
}
