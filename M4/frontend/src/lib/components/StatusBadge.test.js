import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import StatusBadge from './StatusBadge.svelte';
import { statusPresentation } from '#lib/status.js';

describe('canonical status presentation', () => {
	it('keeps overdue and partial-payment meanings distinct', () => {
		expect(statusPresentation('payment_state', 'overdue')).toEqual({
			label: 'Overdue',
			tone: 'danger'
		});
		expect(statusPresentation('payment_state', 'partially_paid')).toEqual({
			label: 'Partially paid',
			tone: 'warning'
		});
		expect(statusPresentation('subscription', 'paused').label).toBe('Paused');
	});
	it('uses text plus an icon and hides non-applicable payment state', async () => {
		const { container, rerender } = render(StatusBadge, { kind: 'invoice', value: 'paid' });
		expect(screen.getByText('Paid')).toBeInTheDocument();
		expect(container.querySelector('svg')).toBeInTheDocument();
		await rerender({ kind: 'payment_state', value: 'not_applicable' });
		expect(container.textContent?.trim()).toBe('');
	});
});
