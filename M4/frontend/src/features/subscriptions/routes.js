// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{
		path: '/app/subscriptions',
		title: 'Subscriptions',
		roles: ['admin', 'staff'],
		component: ComingSoon
	},
	{
		path: '/app/subscriptions/new',
		title: 'New subscription',
		roles: ['admin', 'staff'],
		component: ComingSoon
	},
	{
		path: '/app/subscriptions/:id',
		title: 'Subscription details',
		roles: ['admin', 'staff'],
		component: ComingSoon
	}
];
