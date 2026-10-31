<script>
	import { Dialog as SheetPrimitive } from 'bits-ui';
	/** @type {import('bits-ui').Dialog.TriggerProps} */
	let { ref = $bindable(null), ...restProps } = $props();
</script>

<SheetPrimitive.Trigger bind:ref data-slot="sheet-trigger" {...restProps} />
