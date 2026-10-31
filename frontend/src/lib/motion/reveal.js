import { gsap } from 'gsap';

/** Reveal a mounted subtree, respect reduced motion, and revert on removal. @param {HTMLElement} element */
export function reveal(element) {
	const media = gsap.matchMedia();
	media.add(
		{ motion: '(prefers-reduced-motion: no-preference)' },
		({ conditions }) => {
			if (!conditions?.motion) return;
			gsap.from(element.querySelectorAll('[data-reveal]'), {
				y: 4,
				autoAlpha: 0,
				duration: 0.2,
				stagger: 0.025,
				ease: 'power1.out'
			});
		},
		element
	);
	return () => media.revert();
}
