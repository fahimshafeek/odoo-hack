import SubscriptionList from '../subscriptions/SubscriptionList.svelte';
import SubscriptionDetail from '../subscriptions/SubscriptionDetail.svelte';
import InvoiceList from '../billing/InvoiceList.svelte';
import InvoiceDetail from '../billing/InvoiceDetail.svelte';

export const routes = [
	{
		path: '/portal/subscriptions',
		title: 'My subscriptions',
		roles: ['customer'],
		component: SubscriptionList,
		props: { portal: true }
	},
	{
		path: '/portal/subscriptions/:id',
		title: 'Subscription details',
		roles: ['customer'],
		component: SubscriptionDetail,
		props: { portal: true }
	},
	{
		path: '/portal/invoices',
		title: 'My invoices',
		roles: ['customer'],
		component: InvoiceList,
		props: { portal: true }
	},
	{
		path: '/portal/invoices/:id',
		title: 'Invoice details',
		roles: ['customer'],
		component: InvoiceDetail,
		props: { portal: true }
	}
];
