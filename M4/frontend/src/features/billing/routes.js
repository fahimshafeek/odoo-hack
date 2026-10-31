// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{ path: '/app/invoices', title: 'Invoices', roles: ['admin', 'staff'], component: ComingSoon },
	{
		path: '/app/invoices/:id',
		title: 'Invoice details',
		roles: ['admin', 'staff'],
		component: ComingSoon
	},
	{ path: '/app/payments', title: 'Payments', roles: ['admin', 'staff'], component: ComingSoon },
	{
		path: '/app/billing-runs',
		title: 'Billing runs',
		roles: ['admin', 'staff'],
		component: ComingSoon
	}
];
