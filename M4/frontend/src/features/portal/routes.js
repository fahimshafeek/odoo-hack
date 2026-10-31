// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{
		path: '/portal/subscriptions',
		title: 'My subscriptions',
		roles: ['customer'],
		component: ComingSoon
	},
	{
		path: '/portal/subscriptions/:id',
		title: 'Subscription details',
		roles: ['customer'],
		component: ComingSoon
	},
	{ path: '/portal/invoices', title: 'My invoices', roles: ['customer'], component: ComingSoon },
	{
		path: '/portal/invoices/:id',
		title: 'Invoice details',
		roles: ['customer'],
		component: ComingSoon
	}
];
