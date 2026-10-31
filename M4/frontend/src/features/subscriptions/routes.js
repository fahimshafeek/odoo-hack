import SubscriptionList from './SubscriptionList.svelte';
import SubscriptionDetail from './SubscriptionDetail.svelte';
import SubscriptionForm from './SubscriptionForm.svelte';

export const routes = [
	{
		path: '/app/subscriptions',
		title: 'Subscriptions',
		roles: ['admin', 'staff'],
		component: SubscriptionList
	},
	{
		path: '/app/subscriptions/new',
		title: 'New subscription',
		roles: ['admin', 'staff'],
		component: SubscriptionForm
	},
	{
		path: '/app/subscriptions/:id',
		title: 'Subscription details',
		roles: ['admin', 'staff'],
		component: SubscriptionDetail
	},
	{
		path: '/app/subscriptions/:id/edit',
		title: 'Edit subscription',
		roles: ['admin', 'staff'],
		component: SubscriptionForm
	}
];
