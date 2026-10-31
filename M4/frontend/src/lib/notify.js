import { toast } from 'svelte-sonner';

/** Consistent, readable mutation feedback (A6). */
export const notify = {
	/** @param {string} message */
	success(message) {
		toast.success(message);
	},
	/** @param {unknown} error */
	error(error) {
		toast.error(
			typeof error === 'string'
				? error
				: error instanceof Error
					? error.message
					: 'Something went wrong. Please try again.'
		);
	}
};
