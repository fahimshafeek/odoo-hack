import { describe, it, expect } from 'vitest';
import {
	planSchema,
	termSchema,
	productSchema,
	attributeSchema,
	initialValues,
	writeBody,
	templateSchema
} from './forms.js';

describe('catalog validation and canonical input contracts', () => {
	it('allows optional plan dates and rejects a reversed availability window', () => {
		const values = { ...initialValues('plans'), name: 'Monthly', price: '20.00' };
		expect(planSchema.safeParse(values).success).toBe(true);
		const result = planSchema.safeParse({
			...values,
			valid_from: '2026-12-01',
			valid_to: '2026-11-01'
		});
		expect(result.success).toBe(false);
		if (!result.success) expect(result.error.issues[0].path).toEqual(['valid_to']);
	});
	it('enforces integer payment deadlines between zero and 365', () => {
		expect(termSchema.safeParse({ name: 'Immediate', due_days: 0, is_active: true }).success).toBe(
			true
		);
		expect(termSchema.safeParse({ name: 'Invalid', due_days: 366, is_active: true }).success).toBe(
			false
		);
		expect(termSchema.safeParse({ name: 'Invalid', due_days: 1.5, is_active: true }).success).toBe(
			false
		);
	});
	it('normalizes valid product money and nullable tax', () => {
		const parsed = productSchema.parse({
			...initialValues('products'),
			name: 'Service',
			sales_price: '30',
			cost_price: '0',
			tax_id: ''
		});
		expect(parsed.sales_price).toBe('30.00');
		expect(parsed.tax_id).toBeNull();
		expect(productSchema.safeParse({ ...parsed, sales_price: '10000000' }).success).toBe(false);
	});
	it('rejects duplicate attribute values and retains a known value id', () => {
		const id = '20000000-0000-4000-8000-000000000001';
		expect(
			attributeSchema.parse({ name: 'Size', values: [{ id, name: 'Large', extra_price: '5' }] })
				.values[0].id
		).toBe(id);
		const result = attributeSchema.safeParse({
			name: 'Size',
			values: [
				{ name: 'Large', extra_price: '0' },
				{ name: 'large', extra_price: '0' }
			]
		});
		expect(result.success).toBe(false);
		if (!result.success) expect(result.error.issues[0].path).toEqual(['values', 1, 'name']);
	});
	it('does not send update-only flags in create bodies', () => {
		expect(
			writeBody('payment-terms', { name: 'Net 15', due_days: 15, is_active: true }, false)
		).toEqual({ name: 'Net 15', due_days: 15 });
		expect(writeBody('payment-terms', { is_active: false }, true)).toEqual({ is_active: false });
	});
	it('strips editor keys from template lines while retaining variant selections', () => {
		const id = '20000000-0000-4000-8000-000000000001';
		const parsed = templateSchema.parse({
			...initialValues('quotation-templates'),
			name: 'Template',
			plan_id: id,
			lines: [{ _key: 'local', product_id: id, quantity: 1, variant_value_ids: [id], tax_id: null }]
		});
		expect(parsed.lines[0]).toEqual({
			product_id: id,
			quantity: 1,
			variant_value_ids: [id],
			tax_id: null
		});
	});
});
