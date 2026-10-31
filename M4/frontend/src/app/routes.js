import { routes as auth } from '#src/features/auth/routes.js';
import { routes as staff } from '#src/features/staff/routes.js';
import { routes as customers } from '#src/features/customers/routes.js';
import { routes as dashboard } from '#src/features/dashboard/routes.js';
import { routes as profile } from '#src/features/profile/routes.js';
import { routes as payment_history } from '#src/features/payment-history/routes.js';
import { routes as catalog } from '#src/features/catalog/routes.js';
import { routes as rules } from '#src/features/rules/routes.js';
import { routes as subscriptions } from '#src/features/subscriptions/routes.js';
import { routes as billing } from '#src/features/billing/routes.js';
import { routes as portal } from '#src/features/portal/routes.js';

export const routes = [
	auth,
	staff,
	customers,
	dashboard,
	profile,
	payment_history,
	catalog,
	rules,
	subscriptions,
	billing,
	portal
].flat();

/** Resolve only canonical A6 routes; unknown paths remain 404. @param {string} path */
export function findRoute(path) {
	return routes.find((route) =>
		new RegExp('^' + route.path.replace(/:[^/]+/g, '[^/]+') + '/?$').test(path)
	);
}
