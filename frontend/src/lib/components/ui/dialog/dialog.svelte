<script>
	import { Dialog as DialogPrimitive } from 'bits-ui';
	/** @type {any} */
	let { open = $bindable(false), ...restProps } = $props();
</script>

<DialogPrimitive.Root bind:open {...restProps} />
