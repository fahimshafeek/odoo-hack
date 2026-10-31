/** One canonical status presentation map (A6, SUB-4, INV-4, PAY-1). */
export const statuses = {
	subscription: {
		draft: ['Draft', 'draft'],
		quotation: ['Quotation', 'warning'],
		confirmed: ['Confirmed', 'secondary'],
		active: ['Active', 'active'],
		paused: ['Paused', 'warning'],
		closed: ['Closed', 'draft']
	},
	invoice: {
		draft: ['Draft', 'draft'],
		confirmed: ['Confirmed', 'secondary'],
		paid: ['Paid', 'active'],
		cancelled: ['Cancelled', 'danger']
	},
	payment_state: {
		not_applicable: ['', 'draft'],
		unpaid: ['Unpaid', 'warning'],
		partially_paid: ['Partially paid', 'warning'],
		overdue: ['Overdue', 'danger'],
		paid: ['Paid', 'active']
	},
	active_flag: { true: ['Active', 'active'], false: ['Inactive', 'draft'] }
};

/** @param {keyof typeof statuses} kind @param {string | boolean} value */
export function statusPresentation(kind, value) {
	const mapping = /** @type {Record<string, string[]>} */ (statuses[kind]);
	const [label, tone] = mapping?.[String(value)] ?? ['Unknown', 'draft'];
	return { label, tone };
}
