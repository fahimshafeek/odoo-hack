import AuthScreen from './AuthScreen.svelte';

export const routes = [
	{ path: '/login', title: 'Sign in', roles: [], component: AuthScreen, props: { mode: 'login' } },
	{
		path: '/signup',
		title: 'Create an account',
		roles: [],
		component: AuthScreen,
		props: { mode: 'signup' }
	},
	{
		path: '/forgot-password',
		title: 'Reset your password',
		roles: [],
		component: AuthScreen,
		props: { mode: 'forgot' }
	},
	{
		path: '/reset-password',
		title: 'Choose a new password',
		roles: [],
		component: AuthScreen,
		props: { mode: 'reset' }
	}
];
