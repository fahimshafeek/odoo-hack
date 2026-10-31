import PaymentHistory from './PaymentHistory.svelte';

export const routes = [
	{
		path: '/portal/payments',
		title: 'Payment history',
		roles: ['customer'],
		component: PaymentHistory
	}
];
