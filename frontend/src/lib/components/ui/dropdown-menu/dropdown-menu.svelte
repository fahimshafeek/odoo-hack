<script>
	import { DropdownMenu as DropdownMenuPrimitive } from 'bits-ui';
	/** @type {any} */
	let { open = $bindable(false), ...restProps } = $props();
</script>

<DropdownMenuPrimitive.Root bind:open {...restProps} />
