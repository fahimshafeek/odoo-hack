import { redirect } from '@sveltejs/kit';
import { auth } from '#lib/auth/session.js';
import { routeRedirect } from '#lib/auth/guards.js';

/** Protect the staff workspace (AUTH-4); backend endpoints enforce permissions too. */
export async function load({ url }) {
	await auth.initialize();
	const destination = routeRedirect(auth.user?.role, url.pathname);
	if (destination) redirect(307, destination);
}
