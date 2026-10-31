import {
	LayoutDashboard,
	Repeat2,
	FileText,
	Users,
	ReceiptText,
	Wallet,
	Play,
	Package,
	Layers3,
	CalendarClock,
	Percent,
	Tags,
	UserRoundCog,
	CircleUserRound
} from '@lucide/svelte';

const team = ['admin', 'staff'];
const admin = ['admin'];
const customer = ['customer'];

/** Canonical A6 navigation; roles hide inaccessible links without replacing API RBAC. */
export const navigation = [
	{
		title: 'Overview',
		items: [{ title: 'Dashboard', path: '/app/dashboard', icon: LayoutDashboard, roles: team }]
	},
	{
		title: 'Sales',
		items: [
			{ title: 'Subscriptions', path: '/app/subscriptions', icon: Repeat2, roles: team },
			{
				title: 'Quotation templates',
				path: '/app/quotation-templates',
				icon: FileText,
				roles: admin
			},
			{ title: 'Customers', path: '/app/customers', icon: Users, roles: team }
		]
	},
	{
		title: 'Billing',
		items: [
			{ title: 'Invoices', path: '/app/invoices', icon: ReceiptText, roles: team },
			{ title: 'Payments', path: '/app/payments', icon: Wallet, roles: team },
			{ title: 'Billing runs', path: '/app/billing-runs', icon: Play, roles: team }
		]
	},
	{
		title: 'Catalog',
		items: [
			{ title: 'Products', path: '/app/catalog/products', icon: Package, roles: team },
			{ title: 'Plans', path: '/app/catalog/plans', icon: Layers3, roles: team },
			{
				title: 'Payment terms',
				path: '/app/catalog/payment-terms',
				icon: CalendarClock,
				roles: team
			}
		]
	},
	{
		title: 'Rules',
		items: [
			{ title: 'Taxes', path: '/app/rules/taxes', icon: Percent, roles: team },
			{ title: 'Discounts', path: '/app/rules/discounts', icon: Tags, roles: team }
		]
	},
	{
		title: 'Admin',
		items: [{ title: 'Staff', path: '/app/staff', icon: UserRoundCog, roles: admin }]
	}
];

export const portalNavigation = [
	{
		title: 'Your account',
		items: [
			{ title: 'My subscriptions', path: '/portal/subscriptions', icon: Repeat2, roles: customer },
			{ title: 'My invoices', path: '/portal/invoices', icon: ReceiptText, roles: customer },
			{ title: 'Payment history', path: '/portal/payments', icon: Wallet, roles: customer },
			{ title: 'Profile', path: '/portal/profile', icon: CircleUserRound, roles: customer }
		]
	}
];

/** Select visible groups for the current API-verified role (AUTH-4). @param {string | undefined} role @param {boolean} [portal] */
export function navForRole(role, portal = false) {
	return (portal ? portalNavigation : navigation)
		.map((group) => ({
			...group,
			items: group.items.filter((item) => item.roles.includes(role ?? ''))
		}))
		.filter((group) => group.items.length);
}
