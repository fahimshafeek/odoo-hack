import { setApiTransport } from '../client.js';
import { previewFetch } from './transport.js';
import { auth } from '#lib/auth/session.js';
import { previewSession } from './store.js';

/** Start only from the DEV + VITE_USE_MOCKS guarded client hook. */
export async function startPreview() {
	setApiTransport(previewFetch);
	auth.setSession(previewSession(location.pathname.startsWith('/portal') ? 'customer' : 'admin'));
}
