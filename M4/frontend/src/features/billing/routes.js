import InvoiceList from './InvoiceList.svelte';
import InvoiceDetail from './InvoiceDetail.svelte';
import PaymentsList from './PaymentsList.svelte';
import BillingRuns from './BillingRuns.svelte';

export const routes = [
	{ path: '/app/invoices', title: 'Invoices', roles: ['admin', 'staff'], component: InvoiceList },
	{
		path: '/app/invoices/:id',
		title: 'Invoice details',
		roles: ['admin', 'staff'],
		component: InvoiceDetail
	},
	{ path: '/app/payments', title: 'Payments', roles: ['admin', 'staff'], component: PaymentsList },
	{
		path: '/app/billing-runs',
		title: 'Billing runs',
		roles: ['admin', 'staff'],
		component: BillingRuns
	}
];
