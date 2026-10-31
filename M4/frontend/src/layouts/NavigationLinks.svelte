<script>
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { navForRole } from './navConfig.js';
	import { cn } from '#lib/utils.js';
	/** @type {{role?: string, portal?: boolean, onNavigate?: () => void}} */
	let { role, portal = false, onNavigate = () => {} } = $props();
	const groups = $derived(navForRole(role, portal));
</script>

<nav aria-label={portal ? 'Your account' : 'Workspace'} class="flex flex-col gap-6">
	{#each groups as group (group.title)}
		<div class="flex flex-col gap-2">
			<h2
				class="px-3 text-[0.625rem] font-semibold tracking-widest text-muted-foreground uppercase"
			>
				{group.title}
			</h2>
			{#each group.items as item (item.path)}
				{@const active =
					page.url.pathname === item.path || page.url.pathname.startsWith(`${item.path}/`)}
				<a
					href={resolve('/[...path]', { path: item.path.slice(1) })}
					aria-current={active ? 'page' : undefined}
					onclick={onNavigate}
					class={cn('workspace-link', active && 'workspace-link-active')}
				>
					<item.icon aria-hidden="true" /><span>{item.title}</span>
				</a>
			{/each}
		</div>
	{/each}
</nav>
