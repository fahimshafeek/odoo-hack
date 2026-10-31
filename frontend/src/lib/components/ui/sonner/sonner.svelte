<script>
	import { Loader2, CircleCheck, OctagonX, Info, TriangleAlert } from '@lucide/svelte';
	import { mode } from 'mode-watcher';
	import { Toaster as Sonner } from 'svelte-sonner';
	/** @type {any} */
	let { ...restProps } = $props();
</script>

<Sonner
	theme={mode.current}
	class="toaster group"
	style="--normal-bg: var(--color-popover); --normal-text: var(--color-popover-foreground); --normal-border: var(--color-border);"
	toastOptions={{
		classes: {
			toast: 'cn-toast'
		}
	}}
	{...restProps}
>
	{#snippet loadingIcon()}
		<Loader2 class="size-4 animate-spin" />
	{/snippet}
	{#snippet successIcon()}
		<CircleCheck class="size-4" />
	{/snippet}
	{#snippet errorIcon()}
		<OctagonX class="size-4" />
	{/snippet}
	{#snippet infoIcon()}
		<Info class="size-4" />
	{/snippet}
	{#snippet warningIcon()}
		<TriangleAlert class="size-4" />
	{/snippet}
</Sonner>
