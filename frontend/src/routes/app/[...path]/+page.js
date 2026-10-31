import { error } from '@sveltejs/kit';
import { findRoute } from '#src/app/routes.js';

/** Mount the feature route while keeping unknown paths as 404. */
export function load({ url }) {
	const route = findRoute(url.pathname);
	if (!route) error(404, 'Page not found');
	return { title: route.title };
}
