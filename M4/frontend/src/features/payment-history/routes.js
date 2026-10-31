// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{ path: '/portal/payments', title: 'Payment history', roles: ['customer'], component: ComingSoon }
];
