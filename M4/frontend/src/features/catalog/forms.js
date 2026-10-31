import { z } from 'zod';
import { moneySchema, dateSchema, uuidSchema, quantitySchema } from '#lib/validators.js';

const name = (max = 120) => z.string().trim().min(1, 'Enter a name.').max(max);
const amount = moneySchema.refine(
	(value) => Number(value) <= 9999999.99,
	'Use an amount up to 9,999,999.99.'
);
const optionalDate = dateSchema
	.or(z.literal(''))
	.nullable()
	.transform((value) => value || null);
const optionalId = uuidSchema
	.or(z.literal(''))
	.nullable()
	.transform((value) => value || null);
const active = z.boolean();

export const productSchema = z.object({
	name: name(),
	type: name(40),
	sales_price: amount,
	cost_price: amount,
	notes: z.string().trim().max(2000).nullable(),
	tax_id: optionalId,
	is_active: active
});
export const planSchema = z
	.object({
		name: name(),
		price: amount,
		billing_period: z.enum(['daily', 'weekly', 'monthly', 'yearly']),
		min_quantity: quantitySchema(),
		valid_from: optionalDate,
		valid_to: optionalDate,
		tax_id: optionalId,
		auto_close: z.boolean(),
		allow_early_close: z.boolean(),
		allow_pause: z.boolean(),
		allow_renew: z.boolean(),
		is_active: active
	})
	.superRefine((values, context) => {
		if (values.valid_from && values.valid_to && values.valid_to < values.valid_from)
			context.addIssue({
				code: 'custom',
				path: ['valid_to'],
				message: 'End on or after the start date.'
			});
	});
export const termSchema = z.object({
	name: name(60),
	due_days: z.coerce.number().int('Enter a whole number.').min(0).max(365),
	is_active: active
});
export const templateSchema = z.object({
	name: name(),
	plan_id: uuidSchema,
	validity_days: z.coerce.number().int().min(1).max(365),
	is_active: active,
	lines: z.array(
		z.object({
			product_id: uuidSchema,
			quantity: quantitySchema(),
			variant_value_ids: z.array(uuidSchema),
			tax_id: optionalId
		})
	)
});
export const attributeSchema = z
	.object({
		name: name(80),
		values: z
			.array(z.object({ id: uuidSchema.optional(), name: name(80), extra_price: amount }))
			.min(1, 'Add at least one value.')
	})
	.superRefine((values, context) => {
		const names = new Set();
		values.values.forEach((value, index) => {
			const key = value.name.toLocaleLowerCase();
			if (names.has(key))
				context.addIssue({
					code: 'custom',
					path: ['values', index, 'name'],
					message: 'Use a different value name.'
				});
			names.add(key);
		});
	});

/** @param {string} kind */
export function schemaFor(kind) {
	return kind === 'products'
		? productSchema
		: kind === 'plans'
			? planSchema
			: kind === 'payment-terms'
				? termSchema
				: templateSchema;
}

/** Initialize every field so server dotted errors can be attached to it. @param {string} kind @param {any} [record] */
export function initialValues(kind, record) {
	const common = { name: record?.name ?? '', is_active: record?.is_active ?? true };
	if (kind === 'products')
		return {
			...common,
			type: record?.type ?? 'physical',
			sales_price: record?.sales_price ?? '',
			cost_price: record?.cost_price ?? '',
			notes: record?.notes ?? '',
			tax_id: record?.tax_id ?? record?.tax?.id ?? null
		};
	if (kind === 'plans')
		return {
			...common,
			price: record?.price ?? '',
			billing_period: record?.billing_period ?? 'monthly',
			min_quantity: record?.min_quantity ?? 1,
			valid_from: record?.valid_from ?? '',
			valid_to: record?.valid_to ?? '',
			tax_id: record?.tax_id ?? record?.tax?.id ?? null,
			auto_close: record?.auto_close ?? false,
			allow_early_close: record?.allow_early_close ?? true,
			allow_pause: record?.allow_pause ?? true,
			allow_renew: record?.allow_renew ?? true
		};
	if (kind === 'payment-terms') return { ...common, due_days: record?.due_days ?? 0 };
	return {
		...common,
		plan_id: record?.plan_id ?? record?.plan?.id ?? '',
		validity_days: record?.validity_days ?? 30,
		lines: (record?.lines ?? []).map((/** @type {any} */ line) => ({
			_key: line.id ?? crypto.randomUUID(),
			_product_name: line.product?.name ?? '',
			_tax_name: line.tax?.name ?? '',
			product_id: line.product_id ?? line.product?.id ?? '',
			quantity: line.quantity ?? 1,
			variant_value_ids: line.variant_value_ids ?? line.variant?.value_ids ?? [],
			tax_id: line.tax_id ?? line.tax?.id ?? null
		}))
	};
}

/** Respect create/update differences in the M2 contracts. @param {string} kind @param {any} values @param {boolean} editing */
export function writeBody(kind, values, editing) {
	const body = structuredClone(values);
	if (!editing && (kind === 'payment-terms' || kind === 'quotation-templates'))
		delete body.is_active;
	if (kind === 'products') body.notes = body.notes || null;
	return body;
}

export const catalog = {
	products: {
		title: 'Products',
		singular: 'product',
		description: 'Manage products, prices, and variant options.'
	},
	plans: {
		title: 'Plans',
		singular: 'plan',
		description: 'Set recurring prices and subscription rules.'
	},
	'payment-terms': {
		title: 'Payment terms',
		singular: 'payment term',
		description: 'Set payment deadlines for invoices.'
	},
	'quotation-templates': {
		title: 'Quotation templates',
		singular: 'quotation template',
		description: 'Reuse plans and product lines when creating subscriptions.'
	}
};
