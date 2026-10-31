import Profile from './Profile.svelte';

export const routes = [
	{ path: '/portal/profile', title: 'Your profile', roles: ['customer'], component: Profile }
];
