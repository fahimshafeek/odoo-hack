import { cleanup, fireEvent, render, screen, within } from '@testing-library/svelte';
import { QueryClient, notifyManager } from '@tanstack/svelte-query';
import { tick } from 'svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { request, invalidate, refetchHistory } = vi.hoisted(() => ({
	request: vi.fn(),
	invalidate: vi.fn(),
	refetchHistory: vi.fn()
}));
vi.mock('$app/state', () => ({ page: { url: new URL('http://localhost/app/billing-runs') } }));
vi.mock('$app/navigation', () => ({ goto: vi.fn() }));
vi.mock('$app/paths', () => ({ resolve: (/** @type {string} */ path) => path }));
vi.mock('#src/api/resources.js', () => ({ request }));
vi.mock('#lib/notify.js', () => ({ notify: { success: vi.fn(), error: vi.fn() } }));
vi.mock('#lib/motion/reveal.js', () => ({ reveal: () => {} }));
// The history table is independent of the progress query exercised here.
vi.mock('./api.js', async () => {
	const { readable } = await import('svelte/store');
	return {
		useBillingInvalidation: () => invalidate,
		useBillingRuns: () =>
			readable({
				data: { items: [], total: 0, page: 1, page_size: 25 },
				isPending: false,
				isError: false,
				refetch: refetchHistory
			})
	};
});
import BillingRunsHarness from './__tests__/BillingRunsHarness.svelte';

const progress = {
	id: 'run-test',
	status: 'running',
	total_due: 3,
	processed: 1,
	created: 1,
	skipped: 0,
	failed: 0
};
/** Flush Svelte updates and TanStack's scheduled result notifications without advancing polling. */
async function settle() {
	for (let index = 0; index < 3; index++) {
		await tick();
		await vi.advanceTimersByTimeAsync(0);
	}
}
function progressCalls() {
	return request.mock.calls.filter(
		([method, path]) => method === 'GET' && path === '/billing/runs/run-test'
	);
}

describe('INV-5 billing run progress polling', () => {
	/** @type {QueryClient} */
	let client;
	beforeEach(() => {
		vi.useFakeTimers();
		vi.clearAllMocks();
		// Deliver query notifications as microtasks so only the polling interval uses the fake clock.
		notifyManager.setScheduler((callback) => {
			void Promise.resolve().then(callback);
		});
		client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
	});
	afterEach(() => {
		cleanup();
		client.clear();
		notifyManager.setScheduler((callback) => {
			setTimeout(callback, 0);
		});
		vi.useRealTimers();
	});
	it('starts a run, polls its progress every second, and stops when it finishes', async () => {
		let reads = 0;
		request.mockImplementation(async (/** @type {string} */ method) => {
			if (method === 'POST') return { billing_run_id: 'run-test', status: 'running' };
			reads++;
			return reads === 1
				? progress
				: reads === 2
					? { ...progress, processed: 2 }
					: { ...progress, status: 'finished', processed: 3, created: 2, skipped: 1 };
		});
		render(BillingRunsHarness, { client });
		await fireEvent.click(screen.getByRole('button', { name: 'Run billing' }));
		await settle();
		expect(request).toHaveBeenCalledWith('POST', '/billing/run');
		const current = within(screen.getByRole('region', { name: 'Current billing run' }));
		expect(current.getByText('1 of 3 due subscriptions processed')).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Billing in progress' })).toBeDisabled();
		expect(progressCalls()).toHaveLength(1);
		await vi.advanceTimersByTimeAsync(999);
		await settle();
		expect(progressCalls()).toHaveLength(1);
		await vi.advanceTimersByTimeAsync(1);
		await settle();
		expect(current.getByText('2 of 3 due subscriptions processed')).toBeInTheDocument();
		await vi.advanceTimersByTimeAsync(1000);
		await settle();
		expect(current.getByText('Billing run complete')).toBeInTheDocument();
		expect(current.getByText('3 of 3 due subscriptions processed')).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Run billing' })).toBeEnabled();
		expect(invalidate).toHaveBeenCalledOnce();
		const completedReads = progressCalls().length;
		await vi.advanceTimersByTimeAsync(5000);
		await settle();
		expect(progressCalls()).toHaveLength(completedReads);
	});
	it('aborts an in-flight progress request and stops polling when unmounted', async () => {
		let reads = 0;
		request.mockImplementation(
			(
				/** @type {string} */ method,
				/** @type {string} */ _path,
				/** @type {{signal?: AbortSignal}} */ options = {}
			) => {
				if (method === 'POST') return Promise.resolve({ billing_run_id: 'run-test' });
				if (++reads === 1) return Promise.resolve(progress);
				return new Promise((_resolve, reject) => {
					options.signal?.addEventListener(
						'abort',
						() => reject(new DOMException('Aborted', 'AbortError')),
						{ once: true }
					);
				});
			}
		);
		const { unmount } = render(BillingRunsHarness, { client });
		await fireEvent.click(screen.getByRole('button', { name: 'Run billing' }));
		await settle();
		await vi.advanceTimersByTimeAsync(1000);
		await settle();
		expect(progressCalls()).toHaveLength(2);
		const signal = progressCalls().at(-1)?.[2].signal;
		expect(signal?.aborted).toBe(false);
		unmount();
		await settle();
		expect(signal?.aborted).toBe(true);
		await vi.advanceTimersByTimeAsync(5000);
		await settle();
		expect(progressCalls()).toHaveLength(2);
	});
});
