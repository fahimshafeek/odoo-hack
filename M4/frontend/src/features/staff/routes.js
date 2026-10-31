// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{ path: '/app/staff', title: 'Staff', roles: ['admin'], component: ComingSoon }
];
