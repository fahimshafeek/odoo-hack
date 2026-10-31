<script>
	import { Dialog as DialogPrimitive } from 'bits-ui';
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<DialogPrimitive.Title
	bind:ref
	data-slot="dialog-title"
	class={cn('cn-font-heading text-base leading-none font-medium', className)}
	{...restProps}
/>
