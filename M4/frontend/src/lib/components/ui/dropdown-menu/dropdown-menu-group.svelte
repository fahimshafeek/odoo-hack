<script>
	import { DropdownMenu as DropdownMenuPrimitive } from 'bits-ui';
	/** @type {any} */
	let { ref = $bindable(null), ...restProps } = $props();
</script>

<DropdownMenuPrimitive.Group bind:ref data-slot="dropdown-menu-group" {...restProps} />
