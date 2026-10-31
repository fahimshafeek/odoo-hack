import { render, screen, fireEvent } from '@testing-library/svelte';
import { createRawSnippet } from 'svelte';
import { expect, it, vi } from 'vitest';
import FilterBar from './FilterBar.svelte';

it('shows applied filters and clears only filtering parameters', async () => {
	const onChange = vi.fn();
	const { rerender } = render(FilterBar, {
		children: createRawSnippet(() => ({ render: () => '<span>Filters</span>' })),
		params: { status: 'active', date_from: '2026-10-01', page: 2, sort: '-number' },
		onChange
	});
	expect(screen.getByText('2 active filters')).toBeInTheDocument();
	await fireEvent.click(screen.getByRole('button', { name: 'Remove Status: active filter' }));
	expect(onChange).toHaveBeenLastCalledWith({ status: '' });
	await fireEvent.click(screen.getByRole('button', { name: 'Clear all' }));
	expect(onChange).toHaveBeenLastCalledWith({ status: '', date_from: '' });
	await rerender({ params: { status: '', date_from: '', page: 1 } });
	expect(screen.queryByRole('button', { name: 'Clear all' })).not.toBeInTheDocument();
});
