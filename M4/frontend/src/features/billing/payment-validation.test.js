import { describe, expect, it } from 'vitest';
import { paymentSchema, decimalUnits } from './payment-validation.js';

describe('PAY-1 payment input boundaries', () => {
	it('compares decimal amounts without binary floating-point arithmetic', () => {
		expect(decimalUnits('9999999999.99')).toBe(999999999999n);
		const schema = paymentSchema('100.10', '2026-10-31');
		expect(
			schema.safeParse({ method: 'upi', amount: '100.10', paid_on: '2026-10-31', note: '' }).success
		).toBe(true);
		for (const amount of ['0', '100.11', '-1', '1.001'])
			expect(
				schema.safeParse({ method: 'upi', amount, paid_on: '2026-10-31', note: '' }).success
			).toBe(false);
	});
	it('rejects future dates and supports optional portal amounts', () => {
		expect(
			paymentSchema('100.00', '2026-10-31').safeParse({
				method: 'card',
				amount: '1.00',
				paid_on: '2026-11-01',
				note: ''
			}).success
		).toBe(false);
		expect(paymentSchema('100.00', '2026-10-31', true).parse({ amount: '' })).toEqual({
			amount: undefined
		});
	});
});
