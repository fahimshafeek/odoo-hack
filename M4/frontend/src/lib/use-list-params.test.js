import { describe, expect, it, vi } from 'vitest';
const { current, navigate } = vi.hoisted(() => ({
	current: { url: new URL('http://localhost/app/invoices?page=4&customer_id=customer-1') },
	navigate: vi.fn()
}));
vi.mock('$app/state', () => ({ page: current }));
vi.mock('$app/navigation', () => ({ goto: navigate }));
import { useListParams } from './use-list-params.js';

describe('URL-synced list controls', () => {
	it('preserves resource filters and resets pagination without losing focus', () => {
		const list = useListParams();
		expect(list.value.page).toBe(4);
		list.update({ q: 'customer' });
		const [url, options] = navigate.mock.calls.at(-1) ?? [];
		expect(url.pathname).toBe('/app/invoices');
		expect(url.searchParams.get('customer_id')).toBe('customer-1');
		expect(url.searchParams.get('page')).toBe('1');
		expect(url.searchParams.get('q')).toBe('customer');
		expect(options).toEqual({ reset: false, replace: true });
	});
});
