<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { user, showSidebar, mobile, WEBUI_NAME } from '$lib/stores';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import {
		createTradeTicket,
		getCreditConfig,
		listCreditLog,
		receiveRedemptionCode
	} from '$lib/apis/credit';
	import { toast } from 'svelte-sonner';
	import { getSessionUser } from '$lib/apis/auths';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Modal from '$lib/components/common/Modal.svelte';

	const i18n = getContext('i18n');

	type Model = {
		id: string;
		name: string;
	};
	type APIParams = {
		model: Model;
	};
	type Usage = {
		total_price: number;
		prompt_unit_price: number;
		completion_unit_price: number;
		request_unit_price: number;
		completion_tokens: number;
		prompt_tokens: number;
	};
	type LogDetail = {
		desc: string;
		api_params: APIParams;
		usage: Usage;
	};
	type Log = {
		id: string;
		credit: string;
		detail: LogDetail;
		created_at: number;
	};
	let page = 1;
	let hasMore = true;
	let logs: Array<Log> = [];
	let isLoadingLogs = false;
	
	const loadLogs = async (append: boolean) => {
		isLoadingLogs = true;
		const data = await listCreditLog(localStorage.token, page).catch((error) => {
			toast.error(`${error}`);
			isLoadingLogs = false;
			return null;
		});
		
		if (!data) {
			hasMore = false;
			isLoadingLogs = false;
			return;
		}
		
		if (data.length === 0) {
			hasMore = false;
		} else {
			if (append) {
				logs = [...logs, ...data];
			} else {
				logs = data;
			}
		}
		isLoadingLogs = false;
	};
	const nextLogs = async () => {
		page++;
		await loadLogs(true);
	};

	let credit = 0;
	let payType = 'alipay';
	let payTypes = [
		{
			code: 'alipay',
			title: $i18n.t('Alipay')
		},
		{
			code: 'wxpay',
			title: $i18n.t('WXPay')
		}
	];
	let amount = null;
	let selectedAmount = null;
	
	// 预设充值档位
	const creditOptions = [
		{ amount: 1, popular: false },
		{ amount: 10, popular: false },
		{ amount: 20, popular: false },
		{ amount: 50, popular: false },
		{ amount: 100, popular: true },
		{ amount: 200, popular: false },
		{ amount: 500, popular: false },
		{ amount: 1000, popular: false }
	];

	// redemption code variables
	let redemptionCode = '';
	let isSubmittingRedemption = false;

	// 优惠券
	let couponInput = '';
	let couponCode = '';
	let couponDiscount = 0.95; // 95折
	let couponVerified = null; // null: 未验证, true: 验证成功, false: 验证失败
	let couponMessage = '';

	// 支付弹窗
	let showPaymentModal = false;

	let config = {
		CREDIT_EXCHANGE_RATIO: 0,
		EZFP_PAY_PRIORITY: 'qrcode'
	};

	let tradeInfo = {
		detail: {
			code: -1,
			msg: '',
			payurl: '',
			qrcode: '',
			urlscheme: '',
			img: '',
			imgDisplayUrl: ''
		}
	};

	const showQRCode = (detail: object): Boolean => {
		if (detail?.img) {
			tradeInfo.detail.imgDisplayUrl = detail.img;
			return true;
		}

		if (detail?.qrcode) {
			const qrcodeElement = document.getElementById('trade-qrcode');
			if (qrcodeElement) {
				qrcodeElement.innerHTML = '';
				new QRCode(qrcodeElement, {
					text: detail.qrcode,
					width: 128,
					height: 128,
					colorDark: '#000000',
					colorLight: '#ffffff',
					correctLevel: QRCode.CorrectLevel.H
				});
				return true;
			}
		}

		return false;
	};

	const redirectLink = (detail: object): Boolean => {
		if (detail?.payurl) {
			window.location.href = detail.payurl;
			return true;
		}

		if (detail?.urlscheme) {
			window.location.href = detail.urlscheme;
			return true;
		}

		return false;
	};

	const handleAddCreditClick = async () => {
		const res = await createTradeTicket(localStorage.token, payType, amount).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (res) {
			tradeInfo = res;
			if (tradeInfo.detail === undefined) {
				toast.error('init payment failed');
				return;
			}

			const detail = tradeInfo.detail;
			if (detail?.code !== 1) {
				toast.error(tradeInfo?.detail?.msg);
				return;
			}

			// 显示支付弹窗
			showPaymentModal = true;

			// 延迟生成二维码，等待DOM渲染
			setTimeout(() => {
				if (config.EZFP_PAY_PRIORITY === 'qrcode') {
					if (showQRCode(detail)) {
						return;
					}
					redirectLink(detail);
				} else {
					if (redirectLink(detail)) {
						return;
					}
					showQRCode(detail);
				}
			}, 100);
		}
	};

	const handleWeChatClick = async () => {
		payType = 'wxpay';
		await handleAddCreditClick();
	};

	const handleAlipayClick = async () => {
		payType = 'alipay';
		await handleAddCreditClick();
	};

	const formatDate = (t: number): string => {
		return new Date(t * 1000).toLocaleString();
	};

	const formatDesc = (log: Log): string => {
		const usage = log?.detail?.usage ?? {};
		if (usage && Object.keys(usage).length > 0) {
			if (usage.total_price !== undefined && usage.total_price !== null) {
				return `-${(Math.round(usage.total_price * 1e6) / 1e6).toFixed(7)}`;
			}
			if (usage.request_unit_price) {
				return `-${(usage.request_unit_price / 1e6).toFixed(7)}`;
			}
			if (usage.prompt_unit_price || usage.completion_unit_price) {
				return `-${(Math.round(usage.prompt_tokens * usage.prompt_unit_price + usage.completion_tokens * usage.completion_unit_price) / 1e6).toFixed(7)}`;
			}
		}
		return log?.detail?.desc;
	};

	const doInit = async () => {
		const sessionUser = await getSessionUser(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		await user.set(sessionUser);

		const res = await getCreditConfig(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (res) {
			config = res;
		}

		credit = $user?.credit ? $user?.credit : 0;
		tradeInfo = {};
		const qrcodeElement = document.getElementById('trade-qrcode');
		if (qrcodeElement) {
			qrcodeElement.innerHTML = '';
		}

		await loadLogs(false);
	};

	onMount(async () => {
		await doInit();
	});

	const handleRedeemCode = async () => {
		if (!redemptionCode || !redemptionCode.trim()) {
			toast.error('请输入有效的兑换码');
			return;
		}

		isSubmittingRedemption = true;

		try {
			await receiveRedemptionCode(localStorage.token, redemptionCode.trim());
			toast.success('兑换成功');
			redemptionCode = '';

			// refresh user data and logs
			await doInit();
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			isSubmittingRedemption = false;
		}
	};

	const handleVerifyCoupon = () => {
		if (!couponInput || !couponInput.trim()) {
			couponVerified = null;
			couponMessage = '';
			couponCode = '';
			return;
		}

		// 验证优惠码
		if (couponInput.trim() === 'cheny666') {
			couponVerified = true;
			couponCode = couponInput.trim();
			couponMessage = '优惠码验证成功！付款打95折';
		} else {
			couponVerified = false;
			couponCode = '';
			couponMessage = '优惠码无效';
		}
	};
</script>

<svelte:head>
	<title>
		{$i18n.t('Credit')} • {$WEBUI_NAME}
	</title>
</svelte:head>

<div
	class="relative flex flex-col w-full h-screen max-h-[100dvh] {$showSidebar
		? 'md:max-w-[calc(100%-260px)]'
		: ''} max-w-full"
>
	<nav class="px-2.5 pt-1.5 backdrop-blur-xl">
		<div class="flex items-center gap-1">
			{#if $mobile}
				<div class="{$showSidebar ? 'md:hidden' : ''} self-center flex flex-none items-center">
					<Tooltip
						content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
						interactive={true}
					>
						<button
							class="cursor-pointer flex rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition"
							on:click={() => {
								showSidebar.set(!$showSidebar);
							}}
						>
							<div class="self-center p-1.5">
								<Sidebar />
							</div>
						</button>
				</Tooltip>
			</div>
		{/if}
	</div>
</nav>

	<div class="mt-6 pb-4 px-4 md:px-6 flex-1 overflow-y-auto">
		<div class="max-w-5xl mx-auto py-4">
		<!-- 左右布局 -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6" style="height: calc(100vh - 120px);">
		<!-- 左侧：积分余额和充值区域 -->
		<div class="flex flex-col min-h-0">
			<div class="flex-1 overflow-y-auto px-3 pb-2">
				<div class="space-y-6 min-h-full flex flex-col justify-between">
					<div class="space-y-6">
				<!-- 积分余额 -->
					<div>
						<h2 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">
							余额
						</h2>
						<div class="flex items-baseline gap-1.5">
							<span class="text-3xl font-bold text-gray-900 dark:text-white">{credit}</span>
							<button
								on:click={() => doInit()}
								class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-all"
							>
								<svg
									viewBox="0 0 1024 1024"
									xmlns="http://www.w3.org/2000/svg"
									width="12"
									height="12"
									class="text-gray-400"
								>
									<path
										d="M832 512a32 32 0 0 0-32 32c0 158.784-129.216 288-288 288s-288-129.216-288-288 129.216-288 288-288c66.208 0 129.536 22.752 180.608 64H608a32 32 0 0 0 0 64h160a32 32 0 0 0 32-32V192a32 32 0 0 0-64 0v80.96A350.464 350.464 0 0 0 512 192C317.92 192 160 349.92 160 544s157.92 352 352 352 352-157.92 352-352a32 32 0 0 0-32-32"
										fill="currentColor"
									></path>
								</svg>
							</button>
						</div>
					</div>

					<!-- 积分兑换 -->
					<div>
						<h2 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">
							积分兑换
						</h2>
						<form class="flex items-center gap-2" on:submit|preventDefault={handleRedeemCode}>
							<input
								type="text"
								bind:value={redemptionCode}
								placeholder="请输入兑换码"
								class="flex-1 px-2.5 py-1.5 text-xs bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white rounded-lg outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-white transition-all"
								disabled={isSubmittingRedemption}
							/>
							<button
								type="submit"
								disabled={isSubmittingRedemption || !redemptionCode.trim()}
								class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
							>
								{#if isSubmittingRedemption}
									<Spinner className="size-3" />
								{/if}
								兑换
							</button>
						</form>
					</div>

					<!-- 充值区域 -->
					<div class="space-y-3">
						<h2 class="text-sm font-semibold text-gray-900 dark:text-white">
							积分充值
						</h2>

						<!-- 充值金额标签 -->
						<div class="text-xs text-gray-500 dark:text-gray-400">
							充值金额
						</div>

						<!-- 充值档位选项 -->
						<div class="grid grid-cols-3 gap-2.5">
							{#each creditOptions as option}
								<button
									type="button"
									on:click={() => {
										selectedAmount = option.amount;
										amount = option.amount;
									}}
									class="relative p-3 rounded-lg transition-all {selectedAmount === option.amount
										? 'bg-gray-100 dark:bg-gray-800 ring-2 ring-gray-900 dark:ring-white shadow-sm'
										: 'bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-850'}"
								>
									{#if option.popular}
										<div
											class="absolute -top-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-[10px] rounded-full font-medium"
										>
											{$i18n.t('Popular')}
										</div>
									{/if}
									<div class="text-center">
										<div class="text-base font-semibold text-gray-900 dark:text-white">
											¥{option.amount}
										</div>
										<div class="text-[10px] mt-0.5 text-gray-500 dark:text-gray-400">
											{option.amount * config.CREDIT_EXCHANGE_RATIO} {$i18n.t('Credit')}
										</div>
									</div>
								</button>
							{/each}
							
							<!-- 自定义金额按钮 -->
							<div
								on:click={() => {
									if (selectedAmount !== 'custom') {
										selectedAmount = 'custom';
										amount = null;
									}
								}}
								class="relative p-3 rounded-lg transition-all cursor-pointer {selectedAmount === 'custom'
									? 'bg-gray-100 dark:bg-gray-800 ring-2 ring-gray-900 dark:ring-white shadow-sm'
									: 'bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-850'}"
							>
								<div class="text-center">
									{#if selectedAmount === 'custom'}
										<div class="text-base font-semibold text-gray-900 dark:text-white">
											¥<input
												type="number"
												bind:value={amount}
												on:click|stopPropagation
												class="w-14 text-center bg-transparent outline-none"
												placeholder="0"
												autocomplete="off"
											/>
										</div>
										<div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
											{(amount || 0) * config.CREDIT_EXCHANGE_RATIO} {$i18n.t('Credit')}
										</div>
									{:else}
										<div class="text-base font-semibold text-gray-900 dark:text-white">
											{$i18n.t('Custom')}
										</div>
										<div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
											{$i18n.t('Custom Amount')}
										</div>
									{/if}
								</div>
							</div>
						</div>
					</div>

					<!-- 支付方式 -->
					<div class="space-y-3">
						<!-- 支付方式标签 -->
						<div class="text-xs text-gray-500 dark:text-gray-400">
							支付方式
						</div>

						<!-- 支付方式选择 -->
						<div class="flex items-center gap-2">
							<button
								type="button"
								on:click={() => {
									payType = 'alipay';
								}}
								class="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg transition-all {payType === 'alipay'
									? 'bg-blue-50 dark:bg-blue-950 ring-2 ring-blue-500'
									: 'bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-850'}"
							>
								<img src="/zhifubao.svg" alt="支付宝" class="w-5 h-5" />
								<span class="text-xs font-medium text-gray-900 dark:text-white">支付宝</span>
							</button>

							<button
								type="button"
								on:click={() => {
									payType = 'wxpay';
								}}
								class="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg transition-all {payType === 'wxpay'
									? 'bg-green-50 dark:bg-green-950 ring-2 ring-green-500'
									: 'bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-850'}"
							>
								<img src="/weixinpay.svg" alt="微信支付" class="w-5 h-5" />
								<span class="text-xs font-medium text-gray-900 dark:text-white">微信支付</span>
							</button>
						</div>
					</div>

					<!-- 优惠券 -->
					<div>
						<!-- 优惠券标签 -->
						<div class="text-xs text-gray-500 dark:text-gray-400 mb-2">
							优惠券
						</div>

						<!-- 优惠券输入和验证 -->
						<form class="flex items-center gap-2" on:submit|preventDefault={handleVerifyCoupon}>
							<input
								type="text"
								bind:value={couponInput}
								on:input={() => {
									couponVerified = null;
									couponMessage = '';
									couponCode = '';
								}}
								placeholder="请输入优惠码"
								class="flex-1 px-2.5 py-1.5 text-xs bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white rounded-lg outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-white transition-all"
							/>
							<button
								type="submit"
								disabled={!couponInput.trim()}
								class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
							>
								验证
							</button>
						</form>

						<!-- 验证结果提示 -->
						{#if couponVerified === true}
							<div class="mt-2 text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
								<svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
								</svg>
								<span>{couponMessage}</span>
								{#if amount > 0}
									<span class="text-gray-500 dark:text-gray-400">
										（充值¥{amount}，实付¥{(amount * couponDiscount).toFixed(2)}）
									</span>
								{/if}
							</div>
						{:else if couponVerified === false}
							<div class="mt-2 text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
								<svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
								</svg>
								<span>{couponMessage}</span>
							</div>
					{/if}
				</div>
						</div>
					</div>
			</div>

			<!-- 立即支付按钮 -->
			<div class="px-3">
				<button
					type="button"
					on:click={handleAddCreditClick}
					disabled={!selectedAmount || !amount || amount <= 0}
					class="w-full px-4 py-1.5 text-sm font-semibold bg-gray-900 hover:bg-gray-800 text-white dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100 transition-all rounded-lg shadow-sm disabled:opacity-50 disabled:cursor-not-allowed mt-3"
				>
					立即支付 {amount > 0 ? (couponCode ? `¥${(amount * couponDiscount).toFixed(2)}` : `¥${amount}`) : ''}
				</button>
			</div>
		</div>

				<!-- 右侧：交易记录 -->
				<div class="space-y-3">
					<h2 class="text-sm font-semibold text-gray-900 dark:text-white">
						积分日志
					</h2>

					<div class="space-y-2 overflow-y-auto" style="max-height: calc(100vh - 150px); min-height: 400px;">
						{#if isLoadingLogs && logs.length === 0}
							<div class="flex justify-center items-center py-8">
								<Spinner className="size-4" />
							</div>
						{:else if logs.length > 0}
							{#each logs as log}
								{@const descValue = formatDesc(log)}
								<div
									class="p-2.5 rounded-lg bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-850 transition-all"
								>
									<!-- 第一行：日期和模型 -->
									<div class="flex items-center justify-between mb-1.5">
										<span class="text-[10px] text-gray-500 dark:text-gray-400">
											{formatDate(log.created_at)}
										</span>
										<span class="text-xs text-gray-600 dark:text-gray-300 truncate ml-2">
											{log.detail?.api_params?.model?.name ||
												log.detail?.api_params?.model?.id ||
												$i18n.t('System')}
										</span>
									</div>
									
									<!-- 第二行：积分和描述 -->
									<div class="flex items-center justify-between">
										<span class="text-xs text-gray-600 dark:text-gray-300 font-medium">
											{parseFloat(log.credit).toFixed(6)}
										</span>
										<span
											class="text-xs font-semibold {descValue.toString().startsWith('-')
												? 'text-red-600 dark:text-red-400'
												: 'text-green-600 dark:text-green-400'}"
										>
											{descValue}
										</span>
									</div>
								</div>
							{/each}

							{#if hasMore}
								<button
									class="w-full text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900 transition-all font-medium"
									type="button"
									on:click={() => {
										nextLogs(true);
									}}
								>
									{$i18n.t('Load More')}
								</button>
							{/if}
						{:else}
							<div class="text-center py-12 text-sm text-gray-500 dark:text-gray-400">
								{$i18n.t('No Log')}
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<!-- 支付弹窗 -->
<Modal size="sm" bind:show={showPaymentModal}>
	<div class="p-4">
		<div class="text-center mb-4">
			<h3 class="text-base font-semibold text-gray-900 dark:text-white mb-2">确认支付</h3>
			
			<!-- 支付明细 -->
			<div class="space-y-4 text-xs mb-4">
				<div class="flex items-center justify-between text-gray-600 dark:text-gray-300">
					<span>充值金额</span>
					<span>¥{amount}</span>
				</div>
				{#if couponCode}
					<div class="flex items-center justify-between text-green-600 dark:text-green-400">
						<span>优惠券折扣</span>
						<span>-¥{(amount * (1 - couponDiscount)).toFixed(2)}</span>
					</div>
					<div class="h-px bg-gray-200 dark:bg-gray-700 my-2"></div>
				{/if}
				<div class="flex items-center justify-between font-semibold text-gray-900 dark:text-white">
					<span>实付金额</span>
					<span class="text-sm">{couponCode ? `¥${(amount * couponDiscount).toFixed(2)}` : `¥${amount}`}</span>
				</div>
			</div>
		</div>

		<!-- 二维码显示区域 -->
		{#if tradeInfo?.detail?.qrcode || tradeInfo?.detail?.imgDisplayUrl}
			<div class="flex flex-col items-center p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
				<div
					id="trade-qrcode"
					class="bg-white p-3 rounded {tradeInfo?.detail?.imgDisplayUrl ? 'hidden' : ''}"
				></div>
				{#if tradeInfo?.detail?.imgDisplayUrl}
					<img
						src={tradeInfo?.detail?.imgDisplayUrl}
						alt="trade qrcode"
						class="object-contain max-h-48 max-w-48 rounded"
					/>
				{/if}
				<div class="mt-3 text-xs text-gray-500 dark:text-gray-400">
					请使用{payType === 'alipay' ? '支付宝' : '微信'}扫码支付
				</div>
				<div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
					支付完成后请刷新页面
				</div>
			</div>
		{/if}

		<!-- 关闭按钮 -->
		<div class="mt-4 flex justify-center">
			<button
				on:click={() => {
					showPaymentModal = false;
				}}
				class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-all"
			>
				关闭
			</button>
		</div>
	</div>
</Modal>
