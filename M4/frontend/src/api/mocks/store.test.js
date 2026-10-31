import { describe, expect, it } from 'vitest';
import { createPreviewStore, previewSession } from './store.js';

describe('isolated frontend preview scenarios', () => {
	it('keeps catalog edits, variants and deactivation visible to pickers', () => {
		const store = createPreviewStore();
		const product = store.saveResource('products', {
			name: 'New service',
			sales_price: '500.00',
			cost_price: '200.00',
			type: 'service'
		});
		store.attribute(product.id, {
			name: 'Edition',
			values: [{ name: 'Plus', extra_price: '25.00' }]
		});
		expect(store.product(product.id).attributes[0].values[0].id).toBeTruthy();
		store.saveResource('products', { name: 'Updated service' }, product.id);
		expect(store.list('products', { q: 'Updated service', active: 'true' }).total).toBe(1);
		store.deactivate('products', product.id);
		expect(store.list('products', { q: 'Updated service', active: 'true' }).total).toBe(0);
	});
	it('shares customer contact changes with the profile preview', () => {
		const store = createPreviewStore();
		store.saveProfile({ company_name: 'Updated company', phone: '+91 98765 43210' });
		expect(store.resourceDetail('customers', store.profile().id).company_name).toBe(
			'Updated company'
		);
		const staff = store.saveResource('staff', {
			full_name: 'New member',
			email: 'member@example.test'
		});
		store.saveResource('staff', { is_active: false }, staff.id);
		expect(store.resourceDetail('staff', staff.id).is_active).toBe(false);
	});
	it('provides canonical page shapes and scoped customer rows', () => {
		const store = createPreviewStore();
		const page = store.list('subscriptions', {}, 'customer');
		expect(page.items.length).toBeGreaterThan(0);
		expect(
			page.items.every(
				(row) =>
					row.customer.id === previewSession('customer').user.customer_id && row.status !== 'draft'
			)
		).toBe(true);
		expect(page).toMatchObject({ page: 1, page_size: 25 });
	});
	it('exercises subscription action buttons without a live backend', () => {
		const store = createPreviewStore();
		const active = store
			.list('subscriptions', {}, 'admin')
			.items.find((row) => row.allowed_actions.includes('pause'));
		expect(store.subscriptionAction(active.id, 'pause', 'admin').status).toBe('paused');
		expect(store.subscriptionAction(active.id, 'resume', 'admin').status).toBe('active');
		expect(store.history(active.id).length).toBeGreaterThan(1);
	});
	it('exercises partial/full payment UI states and rejects overpayment', () => {
		const store = createPreviewStore();
		const invoice = store.list('invoices', { payment_filter: 'outstanding' }, 'admin').items[0];
		store.pay(invoice.id, { amount: '1.00', method: 'upi', paid_on: '2026-10-31' }, 'admin');
		const partial = store.invoice(invoice.id, 'admin');
		expect(partial.status).toBe('confirmed');
		expect(() => store.pay(invoice.id, { amount: '9999999.00' }, 'admin')).toThrow();
		store.pay(
			invoice.id,
			{ amount: partial.balance, method: 'upi', paid_on: '2026-10-31' },
			'admin'
		);
		expect(store.invoice(invoice.id, 'admin').status).toBe('paid');
	});
	it('provides a repeatable zero-created billing result for the UI', () => {
		const store = createPreviewStore();
		const first = store.startRun();
		while (store.run(first.id).status === 'running') {
			/* Advance the preview clock by polling. */
		}
		const second = store.startRun();
		let result = store.run(second.id);
		while (result.status === 'running') result = store.run(second.id);
		expect(result.created).toBe(0);
		expect(result.skipped).toBeGreaterThan(0);
	});
});
