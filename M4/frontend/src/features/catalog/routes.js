// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{
		path: '/app/catalog/products',
		title: 'Products',
		roles: ['admin', 'staff'],
		component: ComingSoon
	},
	{ path: '/app/catalog/plans', title: 'Plans', roles: ['admin', 'staff'], component: ComingSoon },
	{
		path: '/app/catalog/payment-terms',
		title: 'Payment terms',
		roles: ['admin', 'staff'],
		component: ComingSoon
	},
	{
		path: '/app/quotation-templates',
		title: 'Quotation templates',
		roles: ['admin'],
		component: ComingSoon
	}
];
