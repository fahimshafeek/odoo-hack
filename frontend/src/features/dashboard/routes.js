import Dashboard from './Dashboard.svelte';

export const routes = [
	{ path: '/app/dashboard', title: 'Overview', roles: ['admin', 'staff'], component: Dashboard }
];
