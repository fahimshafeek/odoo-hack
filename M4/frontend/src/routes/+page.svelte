<script>
	import { resolve } from '$app/paths';
	import {
		ArrowUpRight,
		ArrowRight,
		Repeat2,
		Layers3,
		ReceiptText,
		Wallet,
		Check
	} from '@lucide/svelte';
	import { Button } from '#lib/components/ui/button/index.js';
	import { reveal } from '#lib/motion/reveal.js';
</script>

<svelte:head>
	<title>Brightloop · A better rhythm for your business</title>
	<meta
		name="description"
		content="Keep subscriptions, billing, and payments moving together with Brightloop."
	/>
</svelte:head>

<div class="welcome" {@attach reveal}>
	<header class="welcome-header">
		<a class="brand" href={resolve('/')} aria-label="Brightloop home"
			><span class="brand-symbol"><Repeat2 aria-hidden="true" /></span>brightloop<span
				class="brand-dot">.</span
			></a
		>
		<div class="flex items-center gap-3">
			<span class="hidden text-xs text-muted-foreground sm:block">One workspace. Full clarity.</span
			><Button href="/login" variant="outline" size="sm"
				>Sign in<ArrowUpRight data-icon="inline-end" /></Button
			>
		</div>
	</header>

	<main id="main-content" class="welcome-main">
		<section class="intro">
			<div data-reveal class="intro-label"><span></span>MAKE EVERY CYCLE COUNT</div>
			<h1 data-reveal>Your business.<br />In a better <span>rhythm.</span></h1>
			<p data-reveal class="intro-description">
				From the first subscription to the next renewal. Bring your billing, payments, and customer
				relationships into one clear view.
			</p>
			<div data-reveal class="flex flex-wrap items-center gap-4">
				<Button href="/login" size="lg"
					>Open your workspace<ArrowRight data-icon="inline-end" /></Button
				><Button href="/signup" variant="ghost"
					>Create an account<ArrowUpRight data-icon="inline-end" /></Button
				>
			</div>
			<p data-reveal class="intro-note">
				<Check aria-hidden="true" class="size-4" />Less chasing. More moving forward.
			</p>
		</section>

		<section data-reveal class="cycle-panel" aria-label="Your business cycle, connected">
			<div class="panel-heading">
				<span class="text-xs font-medium text-muted-foreground">THE BRIGHTLOOP WAY</span><span
					class="cycle-tag"><span></span>Always connected</span
				>
			</div>
			<div class="cycle-art" aria-hidden="true">
				<div class="cycle-ring ring-outer"></div>
				<div class="cycle-ring ring-inner"></div>
				<div class="cycle-center"><Repeat2 /><span>One continuous<br />flow.</span></div>
				<span class="orbit-node node-one"><Layers3 /></span><span class="orbit-node node-two"
					><ReceiptText /></span
				><span class="orbit-node node-three"><Wallet /></span>
				<span class="orbit-dot dot-one"></span><span class="orbit-dot dot-two"></span>
			</div>
			<div class="cycle-steps">
				<span><b>01</b>Subscribe</span><ArrowRight aria-hidden="true" /><span><b>02</b>Bill</span
				><ArrowRight aria-hidden="true" /><span><b>03</b>Grow</span>
			</div>
			<p class="panel-caption">A clear next step. At every step.</p>
		</section>
	</main>

	<footer class="welcome-footer">
		<span>Built for the business you’re building.</span><span class="flex items-center gap-2"
			><span class="footer-mark"></span>Subscriptions, beautifully connected.</span
		>
	</footer>
</div>
