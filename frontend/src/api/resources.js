import {
	createMutation,
	createQuery,
	keepPreviousData,
	useQueryClient
} from '@tanstack/svelte-query';
import { toast } from 'svelte-sonner';
import { toStore } from 'svelte/store';
import { api } from '#lib/auth/session.js';
import { notify } from '#lib/notify.js';

/** Central resource boundary. Live contract typing is finalized during integration.
 * @param {'GET' | 'POST' | 'PATCH' | 'DELETE'} method @param {string} path
 * @param {{query?: Record<string, any>, body?: any, signal?: AbortSignal}} [options]
 * @returns {Promise<any>} */
export async function request(method, path, { query, body, signal } = {}) {
	if (!path.startsWith('/') || path.startsWith('//')) throw new Error('Invalid API resource path.');
	const client = /** @type {any} */ (api);
	const options = { params: { query }, signal, ...(body !== undefined ? { body } : {}) };
	const result = await client[method](path, options);
	return result.data;
}

/** @param {string | (() => string)} path */
function readPath(path) {
	return typeof path === 'function' ? path() : path;
}

/** Use server pagination and preserve the current page while filters load (A6).
 * @param {string} scope @param {string | (() => string)} path @param {() => Record<string, any>} readParams */
export function createListQuery(scope, path, readParams) {
	return createQuery(
		toStore(() => {
			const endpoint = readPath(path);
			const query = readParams();
			return {
				queryKey: [scope, endpoint, query],
				queryFn: (/** @type {{signal: AbortSignal}} */ { signal }) =>
					request('GET', endpoint, { query, signal }),
				placeholderData: keepPreviousData
			};
		})
	);
}

/** Read a resource with cancellation when its page is removed.
 * @param {string} scope @param {string | (() => string)} path @param {() => boolean} [readEnabled] */
export function createDetailQuery(scope, path, readEnabled = () => true) {
	return createQuery(
		toStore(() => {
			const endpoint = readPath(path);
			return {
				queryKey: [scope, endpoint],
				enabled: readEnabled(),
				queryFn: (/** @type {{signal: AbortSignal}} */ { signal }) =>
					request('GET', endpoint, { signal })
			};
		})
	);
}

/** Invalidate affected server state and show non-blocking warnings after actions.
 * @param {string} scope @param {'POST' | 'PATCH' | 'DELETE'} method
 * @param {string | ((variables: any) => string)} path
 * @param {(data: any, variables: any) => void | Promise<void>} [onSuccess] */
export function createActionMutation(scope, method, path, onSuccess) {
	const queryClient = useQueryClient();
	return createMutation(
		toStore(() => ({
			mutationFn: (/** @type {{id?: string, body?: any} | undefined} */ variables) =>
				request(method, typeof path === 'function' ? path(variables) : path, {
					body: variables?.body
				}),
			onError: (/** @type {Error} */ error) => notify.error(error),
			onSuccess: async (/** @type {any} */ data, /** @type {any} */ variables) => {
				await Promise.all(
					[scope, 'reports', 'dashboard'].map((key) =>
						queryClient.invalidateQueries({ queryKey: [key] })
					)
				);
				for (const warning of data?.warnings ?? [])
					toast.warning(String(warning).replaceAll('_', ' '));
				await onSuccess?.(data, variables);
			}
		}))
	);
}
