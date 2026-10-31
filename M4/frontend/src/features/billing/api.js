import { useQueryClient } from '@tanstack/svelte-query';
import { createListQuery, createDetailQuery, request } from '#src/api/resources.js';

/** Server-paginated invoices; portal endpoints enforce customer scope (AUTH-4). */
export function useInvoices(
	/** @type {() => boolean} */ portal,
	/** @type {() => Record<string, any>} */ params
) {
	return createListQuery('billing', () => (portal() ? '/me/invoices' : '/invoices'), params);
}

/** Invoice detail and server-owned allowed_actions (INV-3). */
export function useInvoice(/** @type {() => boolean} */ portal, /** @type {() => string} */ id) {
	return createDetailQuery(
		'billing',
		() => `${portal() ? '/me/invoices' : '/invoices'}/${id()}`,
		() => Boolean(id())
	);
}

/** Payment ledger query with server filters (PAY-1). */
export function usePayments(/** @type {() => Record<string, any>} */ params) {
	return createListQuery('billing', '/payments', params);
}

/** Billing run audit trail (INV-5). */
export function useBillingRuns(/** @type {() => Record<string, any>} */ params) {
	return createListQuery('billing', '/billing/runs', params);
}

/** Refetch billing and finance summaries after a successful invoice/payment change. */
export function useBillingInvalidation() {
	const client = useQueryClient();
	return async () => {
		await Promise.all(
			['billing', 'invoices', 'payments', 'reports', 'dashboard', 'portal'].map((scope) =>
				client.invalidateQueries({ queryKey: [scope] })
			)
		);
	};
}

/** Resolve labelled customer choices without loading the entire customer table. */
export async function loadCustomers(/** @type {string} */ query) {
	const result = await request('GET', '/customers', {
		query: { q: query, page: 1, page_size: 100 }
	});
	return (result?.items ?? []).map((/** @type {any} */ customer) => ({
		value: customer.id,
		label: customer.name || customer.company_name || customer.full_name || customer.email
	}));
}
