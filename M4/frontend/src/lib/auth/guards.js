/** Enforce AUTH-4 workspace boundaries; API authorization remains authoritative. @param {string | null | undefined} role @param {string} pathname */
export function routeRedirect(role, pathname) {
	if (!role) {
		return pathname.startsWith('/') && !pathname.startsWith('//')
			? `/login?next=${encodeURIComponent(pathname)}`
			: '/login';
	}
	if (!['admin', 'staff', 'customer'].includes(role)) return '/login';
	if (role === 'customer' && pathname.startsWith('/app')) return '/portal/subscriptions';
	if (role !== 'customer' && pathname.startsWith('/portal')) return '/app/dashboard';
	if (role !== 'admin' && /^\/app\/staff(?:\/|$)/.test(pathname)) return '/app/dashboard';
	return null;
}
