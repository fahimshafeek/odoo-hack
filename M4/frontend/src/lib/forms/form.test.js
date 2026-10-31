import { get } from 'svelte/store';
import { z } from 'zod';
import { describe, expect, it, vi } from 'vitest';
import { applyServerErrors, createForm } from './form.js';

describe('validated form submissions (A6)', () => {
	it('keeps unrelated server errors until the matching field changes', () => {
		const form = createForm({
			schema: z.object({ name: z.string(), note: z.string() }),
			initialValues: { name: 'Team', note: '' }
		});
		applyServerErrors(form, { fields: { name: 'That name is already taken.' } });
		form.setValue('note', 'An unrelated edit');
		expect(get(form).errors.name).toBe('That name is already taken.');
		expect(get(form).isValid).toBe(false);
		form.setValue('name', 'Another team');
		expect(get(form).errors.name).toBeUndefined();
		expect(get(form).isValid).toBe(true);
	});
	it('lets users retry transient failures without changing valid entries', async () => {
		const form = createForm({
			schema: z.object({ name: z.string() }),
			initialValues: { name: 'Team' }
		});
		await form.submit(() => {
			throw new Error('Server unavailable.');
		});
		expect(get(form).formError).toBe('Server unavailable.');
		expect(get(form).isValid).toBe(true);
	});
	it('does not submit invalid values and exposes field errors', async () => {
		const form = createForm({
			schema: z.object({ name: z.string().min(1) }),
			initialValues: { name: '' }
		});
		const submit = vi.fn();
		expect(await form.submit(submit)).toBe(false);
		expect(submit).not.toHaveBeenCalled();
		expect(get(form).errors.name).toBeTruthy();
	});
	it('prevents duplicate submissions while a request is in flight', async () => {
		const form = createForm({
			schema: z.object({ name: z.string() }),
			initialValues: { name: 'Team' }
		});
		let finish = () => {};
		const submit = vi.fn(
			() =>
				new Promise((resolve) => {
					finish = () => resolve(undefined);
				})
		);
		const pending = form.submit(submit);
		await form.submit(submit);
		expect(submit).toHaveBeenCalledOnce();
		expect(get(form).isSubmitting).toBe(true);
		finish();
		await pending;
		expect(get(form).isSubmitting).toBe(false);
	});
	it('maps nested server errors and puts unknown fields at form level', () => {
		const form = createForm({
			schema: z.object({ lines: z.array(z.object({ quantity: z.number() })) }),
			initialValues: { lines: [{ quantity: 1 }] }
		});
		applyServerErrors(form, {
			message: 'Check your entries.',
			fields: { 'lines.0.quantity': 'At least 5 seats.', secret: 'Cannot change this field.' }
		});
		expect(get(form).errors['lines.0.quantity']).toBe('At least 5 seats.');
		expect(get(form).formError).toContain('Cannot change this field.');
		form.setValue('lines.0.quantity', 5);
		expect(get(form).values.lines[0].quantity).toBe(5);
	});
});
