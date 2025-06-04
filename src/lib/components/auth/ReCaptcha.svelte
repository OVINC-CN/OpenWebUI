<script lang="ts">
	import { onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';

	export let siteKey: string;
	export let theme: 'light' | 'dark' = 'light';

	const dispatch = createEventDispatcher();
	
	let recaptchaContainer: HTMLDivElement;
	let widgetId: number | null = null;

	onMount(() => {
		if (!siteKey) {
			console.error('reCAPTCHA site key is required');
			return;
		}

		// 加载reCAPTCHA脚本
		if (!window.grecaptcha) {
			const script = document.createElement('script');
			script.src = 'https://www.recaptcha.net/recaptcha/api.js?onload=onRecaptchaLoad&render=explicit';
			script.async = true;
			script.defer = true;
			document.head.appendChild(script);

			window.onRecaptchaLoad = () => {
				renderRecaptcha();
			};
		} else {
			renderRecaptcha();
		}

		return () => {
			if (widgetId !== null && window.grecaptcha) {
				window.grecaptcha.reset(widgetId);
			}
		};
	});

	function renderRecaptcha() {
		if (window.grecaptcha && recaptchaContainer) {
			widgetId = window.grecaptcha.render(recaptchaContainer, {
				sitekey: siteKey,
				theme: theme,
				callback: handleRecaptchaResponse,
				'expired-callback': handleRecaptchaExpired,
				'error-callback': handleRecaptchaError
			});
		}
	}

	function handleRecaptchaResponse(token: string) {
		dispatch('verified', { token });
	}

	function handleRecaptchaExpired() {
		dispatch('expired');
	}

	function handleRecaptchaError() {
		dispatch('error');
	}

	export function reset() {
		if (widgetId !== null && window.grecaptcha) {
			window.grecaptcha.reset(widgetId);
		}
	}

	// 全局类型声明
	declare global {
		interface Window {
			grecaptcha: any;
			onRecaptchaLoad: () => void;
		}
	}
</script>

<div bind:this={recaptchaContainer} class="recaptcha-container"></div>

<style>
	.recaptcha-container {
		margin: 16px 0;
		display: flex;
		justify-content: center;
	}
</style> 
