import { z } from 'zod';
import { dateSchema, quantitySchema, uuidSchema } from '#lib/validators.js';
import { todayISO } from '#lib/navigation.js';

/** Validate subscription headers and plan constraints without computing prices (SUB-2/3). */
export function subscriptionSchema(/** @type {() => any} */ readPlan) {
	return z
		.object({
			customer_id: uuidSchema,
			plan_id: uuidSchema,
			payment_term_id: uuidSchema,
			start_date: dateSchema,
			expiry_date: dateSchema,
			lines: z.array(
				z.object({
					product_id: uuidSchema,
					quantity: quantitySchema(),
					variant_value_ids: z.array(uuidSchema),
					tax_id: uuidSchema.or(z.literal('')).nullable()
				})
			)
		})
		.superRefine((values, context) => {
			if (values.expiry_date <= values.start_date)
				context.addIssue({
					code: 'custom',
					path: ['expiry_date'],
					message: 'Expiry must be after the start date.'
				});
			const plan = readPlan();
			if (!plan || plan.is_active === false)
				context.addIssue({ code: 'custom', path: ['plan_id'], message: 'Choose an active plan.' });
			if (
				(plan?.valid_from && values.start_date < plan.valid_from) ||
				(plan?.valid_to && values.start_date > plan.valid_to)
			)
				context.addIssue({
					code: 'custom',
					path: ['start_date'],
					message: 'Start inside the plan’s availability dates.'
				});
			values.lines.forEach((line, index) => {
				if (line.quantity < (plan?.min_quantity ?? 1))
					context.addIssue({
						code: 'custom',
						path: ['lines', index, 'quantity'],
						message: `Use at least ${plan.min_quantity}.`
					});
			});
		});
}

/** Seed a local editor from server snapshots; local keys never enter request bodies. */
export function initialSubscription(/** @type {any} */ subscription) {
	return {
		customer_id: subscription?.customer?.id ?? '',
		plan_id: subscription?.plan?.id ?? '',
		payment_term_id: subscription?.payment_term?.id ?? '',
		start_date: subscription?.start_date ?? todayISO(),
		expiry_date: subscription?.expiry_date ?? '',
		lines: (subscription?.lines ?? []).map((/** @type {any} */ line) => ({
			_key: line.id || crypto.randomUUID(),
			_snapshot: line.variant?.selections ?? [],
			product_id: line.product.id,
			quantity: line.quantity,
			variant_value_ids: line.variant_value_ids ?? [],
			tax_id: line.tax?.id ?? null
		}))
	};
}

/** Send only the canonical subscription line input shape (A4). */
export function lineInputs(/** @type {any[]} */ lines) {
	return lines.map((line) => ({
		product_id: line.product_id,
		quantity: line.quantity,
		variant_value_ids: line.variant_value_ids ?? [],
		tax_id: line.tax_id || null
	}));
}
