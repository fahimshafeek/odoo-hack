<script>
	import { DropdownMenu as DropdownMenuPrimitive } from 'bits-ui';
	/** @type {any} */
	let { open = $bindable(false), ...restProps } = $props();
</script>

<DropdownMenuPrimitive.Sub bind:open {...restProps} />
