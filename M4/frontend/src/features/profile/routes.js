// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{ path: '/portal/profile', title: 'Your profile', roles: ['customer'], component: ComingSoon }
];
