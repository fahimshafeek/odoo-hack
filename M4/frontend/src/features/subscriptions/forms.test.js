import { describe, expect, it } from 'vitest';
import { subscriptionSchema, lineInputs } from './forms.js';

describe('subscription form rules (SUB-2, SUB-3)', () => {
	const id = '20000000-0000-4000-8000-000000000001';
	const values = {
		customer_id: id,
		plan_id: id,
		payment_term_id: id,
		start_date: '2026-10-01',
		expiry_date: '2027-10-01',
		lines: [{ product_id: id, quantity: 5, variant_value_ids: [], tax_id: null }]
	};
	const schema = subscriptionSchema(() => ({
		id,
		is_active: true,
		min_quantity: 5,
		valid_from: '2026-01-01',
		valid_to: '2026-12-31'
	}));
	it('accepts an available plan and its minimum quantity', () =>
		expect(schema.safeParse(values).success).toBe(true));
	it('maps invalid dates and quantities onto the corresponding fields', () => {
		const result = schema.safeParse({
			...values,
			expiry_date: values.start_date,
			lines: [{ ...values.lines[0], quantity: 4 }]
		});
		expect(result.success).toBe(false);
		if (!result.success)
			expect(result.error.issues.map((issue) => issue.path.join('.'))).toEqual(
				expect.arrayContaining(['expiry_date', 'lines.0.quantity'])
			);
	});
	it('rejects starts outside plan availability', () =>
		expect(schema.safeParse({ ...values, start_date: '2027-01-01' }).success).toBe(false));
	it('rejects an unavailable plan', () => {
		const unavailable = subscriptionSchema(() => ({ is_active: false }));
		expect(unavailable.safeParse(values).success).toBe(false);
	});
	it('keeps editor metadata out of API inputs and preserves selected variant ids', () => {
		expect(
			lineInputs([
				{
					...values.lines[0],
					_key: 'local',
					_snapshot: [{ attribute: 'Size', value: 'Large' }],
					variant_value_ids: [id],
					tax_id: ''
				}
			])
		).toEqual([{ product_id: id, quantity: 5, variant_value_ids: [id], tax_id: null }]);
	});
});
