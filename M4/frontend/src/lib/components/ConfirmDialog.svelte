<script>
	import * as AlertDialog from './ui/alert-dialog/index.js';
	import { Button } from './ui/button/index.js';
	import ErrorState from './ErrorState.svelte';
	/** @type {{open: boolean, onOpenChange: (open: boolean) => void, title: string, description: string, confirmLabel?: string, destructive?: boolean, onConfirm: () => any | Promise<any>}} */
	let {
		open,
		onOpenChange,
		title,
		description,
		confirmLabel = 'Confirm',
		destructive = false,
		onConfirm
	} = $props();
	let pending = $state(false);
	let error = $state('');
	async function confirm() {
		if (pending) return;
		pending = true;
		error = '';
		try {
			await onConfirm();
			onOpenChange(false);
		} catch (reason) {
			error =
				reason instanceof Error
					? reason.message
					: 'We could not complete this action. Please try again.';
		} finally {
			pending = false;
		}
	}
</script>

<AlertDialog.Root
	{open}
	onOpenChange={(/** @type {boolean} */ next) => {
		if (!pending) {
			error = '';
			onOpenChange(next);
		}
	}}
>
	<AlertDialog.Content
		><AlertDialog.Header
			><AlertDialog.Title>{title}</AlertDialog.Title><AlertDialog.Description
				>{description}</AlertDialog.Description
			></AlertDialog.Header
		>
		{#if error}<ErrorState message={error} />{/if}
		<AlertDialog.Footer
			><AlertDialog.Cancel disabled={pending}>Cancel</AlertDialog.Cancel><Button
				variant={destructive ? 'destructive' : 'default'}
				disabled={pending}
				aria-busy={pending}
				onclick={confirm}>{pending ? 'Working…' : confirmLabel}</Button
			></AlertDialog.Footer
		>
	</AlertDialog.Content>
</AlertDialog.Root>
