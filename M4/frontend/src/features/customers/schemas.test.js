import { describe, it, expect } from 'vitest';
import { createCustomerSchema, customerSchema } from './schemas.js';

describe('customer billing/contact form', () => {
	it('accepts optional contact fields but rejects invalid email and phone', () => {
		const values = {
			full_name: 'Account holder',
			email: 'person@example.com',
			company_name: '',
			phone: '',
			billing_address: '',
			tax_id: ''
		};
		expect(createCustomerSchema.safeParse(values).success).toBe(true);
		expect(createCustomerSchema.safeParse({ ...values, email: 'invalid' }).success).toBe(false);
		expect(createCustomerSchema.safeParse({ ...values, phone: '123' }).success).toBe(false);
		expect(createCustomerSchema.safeParse({ ...values, phone: '+91 98765 43210' }).success).toBe(
			true
		);
	});
	it('limits billing address and tax ID to the backend request bounds', () => {
		const values = { company_name: '', phone: '', billing_address: '', tax_id: '' };
		expect(customerSchema.safeParse({ ...values, billing_address: 'x'.repeat(501) }).success).toBe(
			false
		);
		expect(customerSchema.safeParse({ ...values, tax_id: 'x'.repeat(51) }).success).toBe(false);
	});
});
