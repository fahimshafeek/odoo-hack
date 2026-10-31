<script>
	import { Dialog as SheetPrimitive } from 'bits-ui';
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<SheetPrimitive.Title
	bind:ref
	data-slot="sheet-title"
	class={cn('cn-font-heading text-base font-medium text-foreground', className)}
	{...restProps}
/>
