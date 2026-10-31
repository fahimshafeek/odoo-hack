import { page } from '$app/state';
import { goto } from '$app/navigation';
import { parseListParams, patchListParams } from './list-params.js';

/** Reactive URL-backed server list state. Read `.value` in a derived expression.
 * @param {Record<string, string | number>} [defaults] */
export function useListParams(defaults = {}) {
	return {
		get value() {
			return parseListParams(page.url.searchParams, defaults);
		},
		/** @param {Record<string, string | number>} patch */
		update(patch) {
			const values = patchListParams(parseListParams(page.url.searchParams, defaults), patch);
			const url = new URL(page.url.href);
			for (const [key, value] of Object.entries(values)) {
				if (value === '') url.searchParams.delete(key);
				else url.searchParams.set(key, String(value));
			}
			// This URL is cloned from the current page; its deployment base is already resolved.
			// eslint-disable-next-line svelte/no-navigation-without-resolve
			return goto(url, { reset: false, replace: !Object.hasOwn(patch, 'page') });
		}
	};
}
