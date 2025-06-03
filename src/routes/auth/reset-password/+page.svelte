<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { resetPassword } from '$lib/apis/auths';
	import { toast } from 'svelte-sonner';
	import { getContext, onMount } from 'svelte';

	const i18n = getContext('i18n');

	let token = '';
	let newPassword = '';
	let confirmPassword = '';
	let loading = false;
	let showPassword = false;

	onMount(() => {
		token = $page.url.searchParams.get('token') || '';
		if (!token) {
			toast.error('重置链接无效');
			goto('/auth');
		}
	});

	const handleSubmit = async () => {
		if (!newPassword.trim()) {
			toast.error('请输入新密码');
			return;
		}

		if (newPassword !== confirmPassword) {
			toast.error('两次输入的密码不一致');
			return;
		}

		if (newPassword.length < 8) {
			toast.error('密码长度至少为8位');
			return;
		}

		loading = true;
		try {
			const res = await resetPassword(token, newPassword);
			toast.success(res.message || '密码重置成功');
			goto('/auth');
		} catch (error) {
			toast.error(typeof error === 'string' ? error : '重置失败，请重试');
		} finally {
			loading = false;
		}
	};

	const validatePassword = (password: string) => {
		const hasUpperCase = /[A-Z]/.test(password);
		const hasLowerCase = /[a-z]/.test(password);
		const hasNumbers = /\d/.test(password);
		const hasNonalphas = /\W/.test(password);
		
		return {
			length: password.length >= 8,
			uppercase: hasUpperCase,
			lowercase: hasLowerCase,
			number: hasNumbers,
			special: hasNonalphas
		};
	};

	$: passwordValidation = validatePassword(newPassword);
	$: isValidPassword = Object.values(passwordValidation).every(v => v);
</script>

<svelte:head>
	<title>重置密码 - Open WebUI</title>
</svelte:head>

<div class="fixed inset-0 bg-white dark:bg-gray-900">
	<div class="flex min-h-full">
		<div class="flex flex-1 flex-col justify-center py-12 px-4 sm:px-6 lg:flex-none lg:px-20 xl:px-24">
			<div class="mx-auto w-full max-w-sm lg:w-96">
				<div>
					<h2 class="mt-6 text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
						重置密码
					</h2>
					<p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
						请输入您的新密码
					</p>
				</div>

				<div class="mt-8">
					<form class="space-y-6" on:submit|preventDefault={handleSubmit}>
						<div>
							<label for="new-password" class="block text-sm font-medium text-gray-900 dark:text-white">
								新密码
							</label>
							<div class="mt-1 relative">
								<input
									id="new-password"
									name="new-password"
									type={showPassword ? 'text' : 'password'}
									autocomplete="new-password"
									required
									bind:value={newPassword}
									disabled={loading}
									class="block w-full appearance-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 pr-10 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm text-gray-900 dark:text-white disabled:opacity-50"
									placeholder="请输入新密码"
								/>
								<button
									type="button"
									class="absolute inset-y-0 right-0 pr-3 flex items-center"
									on:click={() => showPassword = !showPassword}
								>
									{#if showPassword}
										<svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
										</svg>
									{:else}
										<svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
										</svg>
									{/if}
								</button>
							</div>
							
							{#if newPassword}
								<div class="mt-2 space-y-1">
									<div class="flex items-center text-xs {passwordValidation.length ? 'text-green-600' : 'text-red-600'}">
										<svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
											{#if passwordValidation.length}
												<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
											{:else}
												<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
											{/if}
										</svg>
										至少8位字符
									</div>
									<div class="flex items-center text-xs {passwordValidation.uppercase ? 'text-green-600' : 'text-gray-400'}">
										<svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
											{#if passwordValidation.uppercase}
												<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
											{:else}
												<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
											{/if}
										</svg>
										包含大写字母
									</div>
									<div class="flex items-center text-xs {passwordValidation.lowercase ? 'text-green-600' : 'text-gray-400'}">
										<svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
											{#if passwordValidation.lowercase}
												<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
											{:else}
												<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
											{/if}
										</svg>
										包含小写字母
									</div>
									<div class="flex items-center text-xs {passwordValidation.number ? 'text-green-600' : 'text-gray-400'}">
										<svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
											{#if passwordValidation.number}
												<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
											{:else}
												<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
											{/if}
										</svg>
										包含数字
									</div>
									<div class="flex items-center text-xs {passwordValidation.special ? 'text-green-600' : 'text-gray-400'}">
										<svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
											{#if passwordValidation.special}
												<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
											{:else}
												<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
											{/if}
										</svg>
										包含特殊字符
									</div>
								</div>
							{/if}
						</div>

						<div>
							<label for="confirm-password" class="block text-sm font-medium text-gray-900 dark:text-white">
								确认密码
							</label>
							<div class="mt-1">
								<input
									id="confirm-password"
									name="confirm-password"
									type="password"
									autocomplete="new-password"
									required
									bind:value={confirmPassword}
									disabled={loading}
									class="block w-full appearance-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm text-gray-900 dark:text-white disabled:opacity-50"
									placeholder="请再次输入密码"
								/>
							</div>
							{#if confirmPassword && newPassword !== confirmPassword}
								<p class="mt-1 text-sm text-red-600">密码不一致</p>
							{/if}
						</div>

						<div>
							<button
								type="submit"
								disabled={loading || !isValidPassword || newPassword !== confirmPassword}
								class="flex w-full justify-center items-center rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
							>
								{#if loading}
									<svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
										<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
										<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
									</svg>
									重置中...
								{:else}
									确认重置密码
								{/if}
							</button>
						</div>
					</form>

					<div class="mt-6">
						<button
							type="button"
							class="w-full flex justify-center py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
							on:click={() => goto('/auth')}
						>
							返回登录页面
						</button>
					</div>
				</div>
			</div>
		</div>
		<div class="relative hidden w-0 flex-1 lg:block">
			<div class="absolute inset-0 bg-gradient-to-br from-blue-600 to-purple-700">
				<div class="absolute inset-0 bg-black bg-opacity-20"></div>
				<div class="absolute inset-0 flex items-center justify-center">
					<div class="text-center text-white">
						<h3 class="text-4xl font-bold mb-4">安全重置</h3>
						<p class="text-xl opacity-90">设置一个强密码保护您的账户</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</div> 
