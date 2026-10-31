import { describe, expect, it } from 'vitest';
import { formatDate, formatMoney } from './format.js';

describe('shared display rules (A6)', () => {
	it('formats server money as INR using Indian grouping', () => {
		expect(formatMoney('1234567.50')).toBe('₹12,34,567.50');
		expect(formatMoney('0.00')).toBe('₹0.00');
		expect(formatMoney(null)).toBe('—');
		expect(formatMoney('invalid')).toBe('—');
	});
	it('keeps date-only values stable and renders timestamps in India', () => {
		expect(formatDate('2026-01-31')).toBe('31 Jan 2026');
		expect(formatDate('2026-01-31T21:00:00Z')).toBe('01 Feb 2026');
		expect(formatDate(null)).toBe('—');
		expect(formatDate('invalid')).toBe('—');
	});
});
