// Phase 0 hand-off: this feature's owner replaces the placeholder component.
import ComingSoon from '#lib/components/ComingSoon.svelte';

export const routes = [
	{ path: '/login', title: 'Sign in', roles: [], component: ComingSoon },
	{ path: '/signup', title: 'Create an account', roles: [], component: ComingSoon },
	{ path: '/forgot-password', title: 'Reset your password', roles: [], component: ComingSoon },
	{ path: '/reset-password', title: 'Choose a new password', roles: [], component: ComingSoon }
];
