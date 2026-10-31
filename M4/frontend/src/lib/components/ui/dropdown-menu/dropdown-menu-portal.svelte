<script>
	import { DropdownMenu as DropdownMenuPrimitive } from 'bits-ui';
	/** @type {any} */
	let { ...restProps } = $props();
</script>

<DropdownMenuPrimitive.Portal {...restProps} />
