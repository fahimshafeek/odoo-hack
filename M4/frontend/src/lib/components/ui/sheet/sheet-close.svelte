<script>
	import { Dialog as SheetPrimitive } from 'bits-ui';
	/** @type {any} */
	let { ref = $bindable(null), ...restProps } = $props();
</script>

<SheetPrimitive.Close bind:ref data-slot="sheet-close" {...restProps} />
