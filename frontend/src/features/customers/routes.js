import CustomerList from './CustomerList.svelte';
import CustomerDetail from './CustomerDetail.svelte';

export const routes = [
	{
		path: '/app/customers',
		title: 'Customers',
		roles: ['admin', 'staff'],
		component: CustomerList
	},
	{
		path: '/app/customers/:id',
		title: 'Customer details',
		roles: ['admin', 'staff'],
		component: CustomerDetail
	}
];
