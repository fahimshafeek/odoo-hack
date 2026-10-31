import CatalogPage from './CatalogPage.svelte';

export const routes = [
	{
		path: '/app/catalog/products',
		title: 'Products',
		roles: ['admin', 'staff'],
		component: CatalogPage,
		props: { kind: 'products' }
	},
	{
		path: '/app/catalog/plans',
		title: 'Plans',
		roles: ['admin', 'staff'],
		component: CatalogPage,
		props: { kind: 'plans' }
	},
	{
		path: '/app/catalog/payment-terms',
		title: 'Payment terms',
		roles: ['admin', 'staff'],
		component: CatalogPage,
		props: { kind: 'payment-terms' }
	},
	{
		path: '/app/quotation-templates',
		title: 'Quotation templates',
		roles: ['admin'],
		component: CatalogPage,
		props: { kind: 'quotation-templates' }
	}
];
