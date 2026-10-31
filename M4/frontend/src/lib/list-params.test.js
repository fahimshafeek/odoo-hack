import { describe, expect, it } from 'vitest';
import { parseListParams, patchListParams } from './list-params.js';

describe('server list URL state (A6)', () => {
	it('normalizes malformed page values and keeps arbitrary filters', () => {
		expect(
			parseListParams(new URLSearchParams('page=NaN&page_size=1000&status=active'))
		).toMatchObject({ page: 1, page_size: 100, status: 'active' });
	});
	it('resets the page on search, sorting, page size, and filter changes', () => {
		const current = { page: 4, page_size: 25, sort: '-created_at', q: '' };
		expect(patchListParams(current, { q: 'team' }).page).toBe(1);
		expect(patchListParams(current, { status: 'active' }).page).toBe(1);
		expect(patchListParams(current, { page: 5 }).page).toBe(5);
	});
});
