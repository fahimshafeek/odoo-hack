import RulePage from './RulePage.svelte';
export const routes = [
	{
		path: '/app/rules/taxes',
		title: 'Taxes',
		roles: ['admin', 'staff'],
		component: RulePage,
		props: { kind: 'taxes' }
	},
	{
		path: '/app/rules/discounts',
		title: 'Discounts',
		roles: ['admin', 'staff'],
		component: RulePage,
		props: { kind: 'discounts' }
	}
];
