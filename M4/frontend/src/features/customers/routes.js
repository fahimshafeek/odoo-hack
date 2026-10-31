// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{ path: '/app/customers', title: 'Customers', roles: ['admin', 'staff'], component: ComingSoon },
	{
		path: '/app/customers/:id',
		title: 'Customer details',
		roles: ['admin', 'staff'],
		component: ComingSoon
	}
];
