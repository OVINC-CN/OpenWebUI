<script lang="ts">
	import { goto } from '$app/navigation';
	import { forgotPassword } from '$lib/apis/auths';
	import { toast } from 'svelte-sonner';
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	let email = '';
	let loading = false;

	const handleSubmit = async () => {
		if (!email.trim()) {
			toast.error('请输入邮箱地址');
			return;
		}

		loading = true;
		try {
			const res = await forgotPassword(email.trim());
			toast.success(res.message || '如果该邮箱地址已注册，您将收到密码重置邮件');
			email = '';
		} catch (error) {
			toast.error(typeof error === 'string' ? error : '发送失败，请稍后重试');
		} finally {
			loading = false;
		}
	};
</script>

<svelte:head>
	<title>忘记密码 - Open WebUI</title>
</svelte:head>

<div class="fixed inset-0 bg-white dark:bg-gray-900">
	<div class="flex min-h-full">
		<div class="flex flex-1 flex-col justify-center py-12 px-4 sm:px-6 lg:flex-none lg:px-20 xl:px-24">
			<div class="mx-auto w-full max-w-sm lg:w-96">
				<div>
					<button
						class="flex items-center text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
						on:click={() => goto('/auth')}
					>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
						</svg>
						返回登录
					</button>
					<h2 class="mt-6 text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
						忘记密码
					</h2>
					<p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
						输入您的邮箱地址，我们将发送密码重置链接给您
					</p>
				</div>

				<div class="mt-8">
					<form class="space-y-6" on:submit|preventDefault={handleSubmit}>
						<div>
							<label for="email" class="block text-sm font-medium text-gray-900 dark:text-white">
								邮箱地址
							</label>
							<div class="mt-1">
								<input
									id="email"
									name="email"
									type="email"
									autocomplete="email"
									required
									bind:value={email}
									disabled={loading}
									class="block w-full appearance-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm text-gray-900 dark:text-white disabled:opacity-50"
									placeholder="请输入您的邮箱地址"
								/>
							</div>
						</div>

						<div>
							<button
								type="submit"
								disabled={loading}
								class="flex w-full justify-center items-center rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
							>
								{#if loading}
									<svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
										<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
										<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
									</svg>
									发送中...
								{:else}
									发送重置邮件
								{/if}
							</button>
						</div>
					</form>

					<div class="mt-6">
						<div class="relative">
							<div class="absolute inset-0 flex items-center">
								<div class="w-full border-t border-gray-300 dark:border-gray-600" />
							</div>
							<div class="relative flex justify-center text-sm">
								<span class="bg-white dark:bg-gray-900 px-2 text-gray-500 dark:text-gray-400">或</span>
							</div>
						</div>

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
		</div>
		<div class="relative hidden w-0 flex-1 lg:block">
			<div class="absolute inset-0 bg-gradient-to-br from-blue-600 to-purple-700">
				<div class="absolute inset-0 bg-black bg-opacity-20"></div>
				<div class="absolute inset-0 flex items-center justify-center">
					<div class="text-center text-white">
						<h3 class="text-4xl font-bold mb-4">密码找回</h3>
						<p class="text-xl opacity-90">安全快捷地重置您的密码</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</div> 
