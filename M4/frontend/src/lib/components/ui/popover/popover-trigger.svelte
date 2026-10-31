<script>
	import { Popover as PopoverPrimitive } from 'bits-ui';
	import { cn } from '#lib/utils.js';
	/** @type {import('bits-ui').Popover.TriggerProps} */
	let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<PopoverPrimitive.Trigger
	bind:ref
	data-slot="popover-trigger"
	class={cn(className)}
	{...restProps}
/>
