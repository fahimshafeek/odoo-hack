import { createQuery } from '@tanstack/svelte-query';
import { toStore } from 'svelte/store';
import { createDetailQuery, createListQuery, request } from '#src/api/resources.js';

/** Read staff or customer subscriptions using server pagination (SUB-2, AUTH-4). */
export function subscriptionsQuery(
	/** @type {() => boolean} */ portal,
	/** @type {() => Record<string, any>} */ params
) {
	return createListQuery(
		'subscriptions',
		() => (portal() ? '/me/subscriptions' : '/subscriptions'),
		params
	);
}

/** Read the role-scoped subscription detail (SUB-4). */
export function subscriptionQuery(
	/** @type {() => boolean} */ portal,
	/** @type {() => string} */ id
) {
	return createDetailQuery(
		'subscriptions',
		() => `${portal() ? '/me/subscriptions' : '/subscriptions'}/${id()}`,
		() => Boolean(id())
	);
}

/** Read an active picker page without downloading the complete resource. */
export function pickerQuery(
	/** @type {string} */ path,
	/** @type {() => boolean} */ enabled = () => true
) {
	return createQuery(
		toStore(() => ({
			queryKey: ['catalog', path, 'picker'],
			enabled: enabled(),
			queryFn: (/** @type {{signal: AbortSignal}} */ { signal }) =>
				request('GET', path, { query: { active: 'true', page_size: 100 }, signal })
		}))
	);
}

/** Search customers asynchronously, using canonical id/label options. */
export async function customerOptions(/** @type {string} */ q) {
	const data = await request('GET', '/customers', { query: { q, page_size: 100 } });
	return (data?.items ?? []).map((/** @type {any} */ item) => ({
		value: item.id,
		label: item.name || item.company_name || item.full_name || item.email
	}));
}
