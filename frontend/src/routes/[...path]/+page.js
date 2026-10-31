import { error, redirect } from '@sveltejs/kit';
import { findRoute } from '#src/app/routes.js';
import { auth } from '#lib/auth/session.js';
import { authDestination } from '#src/features/auth/schemas.js';

/** Mount the feature route while keeping unknown paths as 404. */
export async function load({ url }) {
	const route = findRoute(url.pathname);
	if (!route) error(404, 'Page not found');

	// If already authenticated and visiting auth pages (login/signup), redirect to role workspace
	if (['/login', '/signup'].includes(route.path)) {
		await auth.initialize();
		if (auth.user) {
			const next = authDestination(auth.user.role, url.searchParams.get('next'));
			redirect(307, '/' + next.path + (next.search || ''));
		}
	}

	return { title: route.title };
}
