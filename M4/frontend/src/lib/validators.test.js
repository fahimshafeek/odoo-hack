import { describe, expect, it } from 'vitest';
import {
	dateSchema,
	emailSchema,
	moneySchema,
	passwordChecks,
	passwordSchema,
	phoneSchema,
	quantitySchema
} from './validators.js';

describe('shared input rules (AUTH-2, A6, plan 9.8)', () => {
	it.each(['shortA!', 'alllowercase!', 'ALLUPPERCASE!', 'NoSpecial123'])(
		'rejects an invalid password: %s',
		(value) => {
			expect(passwordSchema.safeParse(value).success).toBe(false);
		}
	);
	it('accepts nine characters with every required class', () => {
		expect(passwordSchema.safeParse('Abcdefg!1').success).toBe(true);
		expect(Object.values(passwordChecks('Abcdefg!1')).every(Boolean)).toBe(true);
		expect(passwordSchema.safeParse(`A!${'a'.repeat(127)}`).success).toBe(false);
	});
	it('normalizes email and validates phones by digit count', () => {
		expect(emailSchema.parse(' Person@Example.com ')).toBe('person@example.com');
		expect(phoneSchema.safeParse('+91 98765 43210').success).toBe(true);
		expect(phoneSchema.safeParse('123-4567').success).toBe(false);
		expect(phoneSchema.safeParse('123456').success).toBe(false);
	});
	it('preserves money as decimal strings and rejects invalid precision', () => {
		expect(moneySchema.parse('1560.5')).toBe('1560.50');
		expect(moneySchema.parse(0)).toBe('0.00');
		for (const value of ['1.001', '-1', '1e4', '10000000000', '']) {
			expect(moneySchema.safeParse(value).success).toBe(false);
		}
	});
	it('checks minimum quantities and real calendar dates', () => {
		expect(quantitySchema(5).safeParse(4).success).toBe(false);
		expect(quantitySchema(5).parse(5)).toBe(5);
		expect(quantitySchema().safeParse(1.5).success).toBe(false);
		expect(dateSchema.safeParse('2026-02-30').success).toBe(false);
		expect(dateSchema.safeParse('2028-02-29').success).toBe(true);
	});
});
