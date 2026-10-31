import { describe, expect, it } from 'vitest';
import { navForRole } from './navConfig.js';

describe('AUTH-4 navigation filtering', () => {
	const paths = (/** @type {string} */ role, portal = false) =>
		navForRole(role, portal).flatMap((group) => group.items.map((item) => item.path));
	it('shows staff read-only catalogs but hides admin-only entries', () => {
		expect(paths('staff')).toContain('/app/catalog/products');
		expect(paths('staff')).not.toContain('/app/staff');
		expect(paths('staff')).not.toContain('/app/quotation-templates');
		expect(paths('admin')).toContain('/app/staff');
	});
	it('isolates customer navigation and rejects unknown roles', () => {
		expect(paths('customer')).toEqual([]);
		expect(paths('customer', true)).toContain('/portal/invoices');
		expect(paths('admin', true)).toEqual([]);
		expect(paths('unknown')).toEqual([]);
	});
});
