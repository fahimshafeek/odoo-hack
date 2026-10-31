import { render, screen, fireEvent, within } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import DataTable from './DataTable.svelte';

const params = { page: 1, page_size: 25, sort: '-number', q: '' };
const columns = [
	{ key: 'number', header: 'Number', sortKey: 'number' },
	{ key: 'name', header: 'Customer' }
];
const data = {
	items: [{ id: 'row-1', number: 'SUB-001', name: 'A customer' }],
	total: 26,
	page: 1,
	page_size: 25
};

describe('shared server-paginated table (A6)', () => {
	it('renders loading, empty and error states with retry', async () => {
		const onRetry = vi.fn();
		const { rerender } = render(DataTable, {
			columns,
			params,
			onParamsChange: vi.fn(),
			isLoading: true,
			onRetry
		});
		expect(screen.getByRole('status', { name: 'Loading records' })).toBeInTheDocument();
		await rerender({ isLoading: false });
		expect(screen.getByText('No records found')).toBeInTheDocument();
		await rerender({ isError: true });
		await fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
		expect(onRetry).toHaveBeenCalledOnce();
	});
	it('requests server sorting and pages without reordering data locally', async () => {
		const onParamsChange = vi.fn();
		render(DataTable, { columns, data, params, onParamsChange });
		expect(screen.getByRole('columnheader', { name: 'Number' })).toHaveAttribute(
			'aria-sort',
			'descending'
		);
		await fireEvent.click(screen.getByRole('button', { name: 'Number' }));
		expect(onParamsChange).toHaveBeenLastCalledWith({ sort: 'number' });
		await fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
		expect(onParamsChange).toHaveBeenLastCalledWith({ page: 2 });
		expect(screen.getByRole('button', { name: 'Previous page' })).toBeDisabled();
	});
	it('provides labelled mobile cards and a keyboard-accessible row action', async () => {
		const onRowClick = vi.fn();
		render(DataTable, { columns, data, params, onRowClick, onParamsChange: vi.fn() });
		const cards = within(screen.getByTestId('mobile-records'));
		expect(cards.getByText('Customer')).toBeInTheDocument();
		expect(cards.getByText('A customer')).toBeInTheDocument();
		await fireEvent.click(screen.getByRole('button', { name: 'SUB-001' }));
		expect(onRowClick).toHaveBeenCalledWith(data.items[0]);
	});
});
