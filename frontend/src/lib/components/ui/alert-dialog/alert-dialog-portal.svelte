<script>
	import { AlertDialog as AlertDialogPrimitive } from 'bits-ui';
	/** @type {any} */
	let { ...restProps } = $props();
</script>

<AlertDialogPrimitive.Portal {...restProps} />
