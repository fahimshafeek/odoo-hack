import { redirect } from '@sveltejs/kit';
import { auth } from '#lib/auth/session.js';
import { routeRedirect } from '#lib/auth/guards.js';

/** Protect the customer's portal (AUTH-4); backend scopes records to their owner. */
export async function load({ url }) {
	await auth.initialize();
	const destination = routeRedirect(auth.user?.role, url.pathname);
	if (destination) redirect(307, destination);
}
