import { render, screen, within } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import RevenueChart from './RevenueChart.svelte';

describe('dashboard revenue chart', () => {
	it('provides a labelled graph and exact amounts in an accessible data table', () => {
		render(RevenueChart, {
			rows: [{ month: '2026-10', invoiced: '1234.56', collected: '1000.00' }]
		});
		expect(
			screen.getByRole('img', { name: /Monthly invoiced and collected revenue/ })
		).toBeInTheDocument();
		const table = within(screen.getByRole('table', { hidden: true }));
		expect(table.getByText('October 2026')).toBeInTheDocument();
		expect(table.getByText('₹1,234.56')).toBeInTheDocument();
		expect(table.getByText('₹1,000.00')).toBeInTheDocument();
	});
	it('renders a zero-revenue month without invalid SVG coordinates', () => {
		const { container } = render(RevenueChart, {
			rows: [{ month: '2026-10', invoiced: '0.00', collected: '0.00' }]
		});
		const bars = container.querySelectorAll('rect');
		expect(bars).toHaveLength(2);
		for (const bar of bars) {
			expect(bar.getAttribute('height')).toBe('0');
			expect(Number.isFinite(Number(bar.getAttribute('y')))).toBe(true);
		}
	});
});
