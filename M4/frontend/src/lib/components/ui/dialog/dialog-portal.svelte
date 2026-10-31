<script>
	import { Dialog as DialogPrimitive } from 'bits-ui';
	/** @type {any} */
	let { ...restProps } = $props();
</script>

<DialogPrimitive.Portal {...restProps} />
