import { render, screen, fireEvent } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import SearchInput from './SearchInput.svelte';

describe('debounced search', () => {
	afterEach(() => vi.useRealTimers());
	it('waits 300ms, keeps the latest query, and cancels on removal', async () => {
		vi.useFakeTimers();
		const onChange = vi.fn();
		const { unmount } = render(SearchInput, { value: '', onChange });
		const input = screen.getByRole('searchbox');
		await fireEvent.input(input, { target: { value: 'Ac' } });
		await vi.advanceTimersByTimeAsync(200);
		await fireEvent.input(input, { target: { value: 'Acme' } });
		await vi.advanceTimersByTimeAsync(299);
		expect(onChange).not.toHaveBeenCalled();
		await vi.advanceTimersByTimeAsync(1);
		expect(onChange).toHaveBeenLastCalledWith('Acme');
		await fireEvent.input(input, { target: { value: 'Next' } });
		unmount();
		await vi.advanceTimersByTimeAsync(500);
		expect(onChange).toHaveBeenCalledTimes(1);
	});
});
