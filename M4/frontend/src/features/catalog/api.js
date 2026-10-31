import { createQuery } from '@tanstack/svelte-query';
import { toStore } from 'svelte/store';
import { request } from '#src/api/resources.js';

/** Active, paginated pickers share catalog invalidation with edits. @param {string} path @param {() => boolean} [enabled] */
export function picker(path, enabled = () => true) {
	return createQuery(
		toStore(() => ({
			queryKey: ['catalog', path, 'picker'],
			enabled: enabled(),
			queryFn: (/** @type {{signal:AbortSignal}} */ { signal }) =>
				request('GET', path, { query: { active: 'true', page_size: 100, sort: 'name' }, signal })
		}))
	);
}
