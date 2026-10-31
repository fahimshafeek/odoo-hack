// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{ path: '/app/rules/taxes', title: 'Taxes', roles: ['admin', 'staff'], component: ComingSoon },
	{
		path: '/app/rules/discounts',
		title: 'Discounts',
		roles: ['admin', 'staff'],
		component: ComingSoon
	}
];
