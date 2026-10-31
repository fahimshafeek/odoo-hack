<script>
	import WorkspaceShell from './WorkspaceShell.svelte';
	/** @type {{children: import('svelte').Snippet}} */
	let { children } = $props();
</script>

<WorkspaceShell portal>{@render children()}</WorkspaceShell>
