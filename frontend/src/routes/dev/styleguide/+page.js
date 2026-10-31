import { error } from '@sveltejs/kit';

/** Keep the component workshop outside the production product (B2). */
export function load() {
	if (!import.meta.env.DEV) error(404, 'Page not found');
	return {};
}
