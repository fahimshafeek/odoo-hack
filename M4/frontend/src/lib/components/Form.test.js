import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import { z } from 'zod';
import { applyServerErrors, createForm } from '#lib/forms/form.js';
import FormFixture from './__tests__/FormFixture.svelte';

describe('shared Svelte form controls (A6)', () => {
	const make = () =>
		createForm({
			schema: z.object({
				name: z.string().min(1, 'Enter your name.'),
				lines: z.array(z.object({ quantity: z.number().int().min(5) }))
			}),
			initialValues: { name: 'Team', lines: [{ quantity: 5 }] }
		});
	it('shows field errors and disables an invalid form', async () => {
		const onSubmit = vi.fn();
		render(FormFixture, { form: make(), onSubmit });
		await fireEvent.input(screen.getByLabelText(/Name/), { target: { value: '' } });
		expect(screen.getByText('Enter your name.')).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
		expect(onSubmit).not.toHaveBeenCalled();
	});
	it('maps dotted server errors to the matching accessible input', async () => {
		const form = make();
		render(FormFixture, { form, onSubmit: vi.fn() });
		applyServerErrors(form, { fields: { 'lines.0.quantity': 'At least 5 seats.' } });
		expect(await screen.findByText('At least 5 seats.')).toBeInTheDocument();
		expect(screen.getByLabelText(/Quantity/)).toHaveAttribute('aria-invalid', 'true');
	});
});
