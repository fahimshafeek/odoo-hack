/** @typedef {{page: number, page_size: number, sort: string, q: string} & Record<string, string | number>} ListParams */

/** Read bounded server pagination plus arbitrary resource filters (A6).
 * @param {Iterable<[string, string]>} search @param {Record<string, string | number>} [defaults] @returns {ListParams} */
export function parseListParams(search, defaults = {}) {
	const all = {
		page: 1,
		page_size: 25,
		sort: '-created_at',
		q: '',
		...defaults,
		...Object.fromEntries(search)
	};
	const positive = (/** @type {unknown} */ value, /** @type {number} */ fallback) =>
		Number.isInteger(Number(value)) && Number(value) > 0 ? Number(value) : fallback;
	return {
		...all,
		page: positive(all.page, 1),
		page_size: Math.min(100, positive(all.page_size, 25))
	};
}

/** Reset pagination when a filter changes. @param {ListParams} current @param {Record<string, string | number>} patch @returns {ListParams} */
export function patchListParams(current, patch) {
	const changedFilter = Object.keys(patch).some(
		(key) => key !== 'page' && patch[key] !== current[key]
	);
	const values = { ...current, ...patch, ...(changedFilter ? { page: 1 } : {}) };
	return parseListParams(
		new URLSearchParams(Object.entries(values).map(([key, value]) => [key, String(value)]))
	);
}
