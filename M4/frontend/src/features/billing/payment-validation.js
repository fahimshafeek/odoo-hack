import { z } from 'zod';
import { dateSchema, moneySchema, notesSchema } from '#lib/validators.js';

/** Compare PAY-1 input bounds in integer minor units; pricing remains server-owned. */
export function decimalUnits(/** @type {string} */ value) {
	const [whole, fraction = ''] = value.split('.');
	return BigInt(whole || '0') * 100n + BigInt(fraction.padEnd(2, '0'));
}

/** India calendar date matches the backend clock (D13). */
export function indiaToday() {
	const parts = new Intl.DateTimeFormat('en-CA', {
		timeZone: 'Asia/Kolkata',
		year: 'numeric',
		month: '2-digit',
		day: '2-digit'
	}).formatToParts(new Date());
	const value = (/** @type {string} */ type) =>
		parts.find((part) => part.type === type)?.value ?? '';
	return `${value('year')}-${value('month')}-${value('day')}`;
}

/** Validate PAY-1 positivity, balance limit, date and note before submitting. */
export function paymentSchema(
	/** @type {string} */ balance,
	/** @type {string} */ today,
	portal = false
) {
	const amount = moneySchema.refine(
		(value) => decimalUnits(value) > 0n && decimalUnits(value) <= decimalUnits(balance),
		'Enter an amount above zero and no more than the balance.'
	);
	return portal
		? z.object({ amount: z.union([z.literal('').transform(() => undefined), amount]) })
		: z.object({
				method: z.enum(['cash', 'bank_transfer', 'card', 'upi', 'cheque', 'online']),
				amount,
				paid_on: dateSchema.refine(
					(value) => value <= today,
					'Payment date cannot be in the future.'
				),
				note: notesSchema(500)
			});
}
