<script>
	import { DropdownMenu as DropdownMenuPrimitive } from 'bits-ui';
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, inset, ...restProps } = $props();
</script>

<DropdownMenuPrimitive.GroupHeading
	bind:ref
	data-slot="dropdown-menu-group-heading"
	data-inset={inset}
	class={cn('px-1.5 py-1 text-xs font-medium text-muted-foreground data-inset:pl-7', className)}
	{...restProps}
/>
