import { gsap } from 'gsap';

/** Reveal a mounted subtree, respect reduced motion, and revert on removal. @param {HTMLElement} element */
export function reveal(element) {
	const media = gsap.matchMedia();
	media.add(
		{ motion: '(prefers-reduced-motion: no-preference)' },
		({ conditions }) => {
			if (!conditions?.motion) return;
			gsap.from(element.querySelectorAll('[data-reveal]'), {
				y: 16,
				autoAlpha: 0,
				duration: 0.65,
				stagger: 0.09,
				ease: 'power3.out'
			});
		},
		element
	);
	return () => media.revert();
}
