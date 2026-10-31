<script>
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import {
		Menu,
		Repeat2,
		ChevronDown,
		LogOut,
		CircleUserRound,
		ChevronRight
	} from '@lucide/svelte';
	import { auth } from '#lib/auth/session.js';
	import { findRoute } from '#src/app/routes.js';
	import { cn } from '#lib/utils.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import * as Sheet from '#lib/components/ui/sheet/index.js';
	import * as DropdownMenu from '#lib/components/ui/dropdown-menu/index.js';
	import NavigationLinks from './NavigationLinks.svelte';
	/** @type {{children: import('svelte').Snippet, portal?: boolean}} */
	let { children, portal = false } = $props();
	let mobileOpen = $state(false);
	const user = $derived($auth.user);
	const title = $derived(findRoute(page.url.pathname)?.title ?? 'Workspace');
	const initials = $derived(
		user?.full_name
			.split(/\s+/)
			.filter(Boolean)
			.slice(0, 2)
			.map((part) => part[0])
			.join('') || 'B'
	);
</script>

<svelte:window
	onresize={() => {
		if (innerWidth >= 1024) mobileOpen = false;
	}}
/>

<div class={cn('workspace-shell', portal && 'portal-shell')}>
	<aside class="workspace-sidebar">
		<a href={resolve('/')} class="brand workspace-brand"
			><span class="brand-symbol"><Repeat2 aria-hidden="true" /></span>Brightloop</a
		>
		<NavigationLinks role={user?.role} {portal} />
	</aside>
	<div class="workspace-body">
		<header class="workspace-topbar">
			<div class="flex min-w-0 items-center gap-3">
				<div class="lg:hidden">
					<Sheet.Root bind:open={mobileOpen}>
						<Sheet.Trigger>
							{#snippet child({ props })}<Button
									{...props}
									variant="ghost"
									size="icon"
									aria-label="Open navigation"><Menu /></Button
								>{/snippet}
						</Sheet.Trigger>
						<Sheet.Content side="left" class="w-72 overflow-y-auto p-6">
							<Sheet.Header class="mb-4 p-0"
								><Sheet.Title>Brightloop</Sheet.Title><Sheet.Description
									>{portal ? 'Your account' : 'Your workspace'}</Sheet.Description
								></Sheet.Header
							>
							<NavigationLinks role={user?.role} {portal} onNavigate={() => (mobileOpen = false)} />
						</Sheet.Content>
					</Sheet.Root>
				</div>
				<nav
					aria-label="Breadcrumb"
					class="flex min-w-0 items-center gap-2 text-xs text-muted-foreground"
				>
					<span class="hidden sm:inline">{portal ? 'My account' : 'Workspace'}</span><ChevronRight
						class="hidden size-3 sm:block"
						aria-hidden="true"
					/><span class="truncate text-foreground" aria-current="page">{title}</span>
				</nav>
			</div>
			<div class="flex shrink-0 items-center gap-3">
				<Badge variant="secondary">{user?.role ?? 'Account'}</Badge>
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}<Button {...props} variant="ghost" aria-label="Account menu"
								><span class="account-avatar">{initials}</span><span
									class="hidden max-w-40 truncate sm:inline"
									>{user?.full_name ?? 'Your account'}</span
								><ChevronDown data-icon="inline-end" /></Button
							>{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="end" class="w-60">
						<DropdownMenu.Group>
							<DropdownMenu.GroupHeading
								>{user?.full_name ?? 'Your account'}</DropdownMenu.GroupHeading
							>
							<DropdownMenu.Label class="truncate">{user?.email ?? ''}</DropdownMenu.Label>
							{#if portal}<DropdownMenu.Item
									href={resolve('/[...path]', { path: 'portal/profile' })}
									><CircleUserRound />Profile</DropdownMenu.Item
								>{/if}
							<DropdownMenu.Item onclick={() => auth.logout()}><LogOut />Sign out</DropdownMenu.Item
							>
						</DropdownMenu.Group>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
			</div>
		</header>
		<div class="workspace-content">{@render children()}</div>
	</div>
</div>
