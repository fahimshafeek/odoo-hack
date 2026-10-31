import { z } from 'zod';
import { emailSchema, personNameSchema, notesSchema, phoneSchema } from '#lib/validators.js';

export const customerSchema = z.object({
	company_name: notesSchema(120),
	phone: z.union([z.literal(''), phoneSchema]),
	billing_address: notesSchema(500),
	tax_id: notesSchema(50)
});
export const createCustomerSchema = customerSchema.extend({
	email: emailSchema,
	full_name: personNameSchema
});
/** Editable contact fields from M1's CustomerUpdateRequest. @param {any} customer */
export function customerValues(customer = {}) {
	return {
		company_name: customer.company_name ?? '',
		phone: customer.phone ?? '',
		billing_address: customer.billing_address ?? '',
		tax_id: customer.tax_id ?? ''
	};
}
/** Canonical customer IDs remain separate from linked user IDs. @param {any} customer */
export function customerName(customer) {
	return customer.company_name || customer.full_name || customer.email || 'Customer';
}
