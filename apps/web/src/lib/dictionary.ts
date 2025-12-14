export type Locale = 'es' | 'en';

export const dictionary = {
    es: {
        // Navbar
        nav_home: "Inicio",
        nav_guide: "Guía",
        nav_connect: "Conectar",

        // Page
        hero_badge: "BETA PÚBLICA",
        hero_title: "Premios Virales en",
        hero_subtitle: "Farcaster",
        hero_description: "Recompensas Virales en Farcaster",
        powered_by: "powered by",

        // Leaderboard
        trends_title: "Tendencias Activas",
        trends_refresh: "Actualizar Tendencias",
        trends_available_in: "Disponible en",
        trends_empty: "Sin tendencias recientes.",
        trend_rank: "Trend",
        trend_by: "Por",
        trend_join: "Sumate a la tendencia",
        leaderboard_title: "Top Ganadores (24h)",
        leaderboard_empty: "Aún no hay ganadores.",
        leaderboard_pending: "Pendiente",

        // Campaign Form
        form_action_placeholder: "Ingresa el enlace del cast de Farcaster...",
        form_verify_btn: "Verificar Requisitos",
        form_analyze_btn: "Analizar y Reclamar",
        form_cooldown: "Enfriamiento:",
        form_recharge_btn: "Recargar Energía",
        form_energy_empty: "¡Sin Energía! 🔋",
        form_energy_desc: "Debes esperar para el siguiente loot.",
        form_energy_ask: "¿Quieres recargar instantáneamente?",
        form_share_btn: "Compartir para Recargar",
        form_wait_btn: "Esperar",
        form_error_no_url: "Por favor ingresa una URL válida",
        form_status_scan: "Escaneando...",
        form_status_analysis: "Analizando...",
        form_status_verify: "Verificando...",
        form_status_send: "Enviando...",
        form_status_done: "¡Completado!",

        // Reward Types
        reward_nft: "Loot NFT",
        reward_cusd: "MiniPay Drop",
        reward_xp: "XP Boost",

        // Analysis Overlay
        overlay_step1: "Analizando cast...",
        overlay_step2: "Verificando elegibilidad...",
        overlay_step3: "Generando recompensa...",
        overlay_step4: "Finalizando transacción...",
        overlay_success: "¡Recompensa Reclamada!",
        overlay_failed: "No elegible / Falló",
        overlay_view_tx: "Ver Transacción",
        overlay_close: "Cerrar",

        // Settings
        settings_theme_light: "Claro",
        settings_theme_dark: "Oscuro",
        settings_lang: "Idioma",

        // Cast Generator
        cast_select_topic: "Selecciona un Tema",
        cast_select_topic_desc: "Elige el tema para tu cast",
        cast_generate_title: "Generar Cast con IA",
        cast_generate_desc: "Usa inteligencia artificial para crear contenido viral",
        cast_generating: "Generando...",
        cast_generate_btn: "Generar Cast",
        cast_generated: "Cast Generado",
        cast_characters: "caracteres",
        cast_schedule_title: "Programar para más tarde (Opcional)",
        cast_schedule_will_publish: "Se publicará el",
        cast_publish_btn: "Publicar por 1 CELO",
        cast_confirming_payment: "Confirmando pago...",
        cast_publishing: "Publicando...",
        cast_published_success: "¡Cast publicado exitosamente! Ganaste 100 XP",
        cast_success_note: "El cast se publicó automáticamente en tu perfil de Farcaster usando tu signer aprobado.",
        cast_view_tx: "Ver transacción en CeloScan",
        cast_price: "Precio: 1 CELO",
        cast_price_desc: "Por cada cast publicado recibirás",
        cast_price_xp: "100 XP",
        cast_price_reward: "como recompensa",
        cast_loading_address: "Cargando dirección del agente...",
        cast_error_backend: "Backend no configurado. Verifica NEXT_PUBLIC_AGENT_SERVICE_URL",
        cast_error_generating: "Error generando cast",
        cast_error_publishing: "Error publicando cast",
        cast_error_payment: "Error iniciando pago",
        cast_error_address: "Error obteniendo dirección del agente:",
        cast_error_signer_required: "Se requiere aprobar un signer para publicar casts. Por favor, aprueba el signer en Warpcast y luego vuelve a esta app.",
        cast_approval_url: "Enlace de aprobación",
        cast_approval_note: "Se abrirá Warpcast para que apruebes el signer. Después de aprobar, vuelve aquí para continuar.",

        // Scheduled Casts
        scheduled_title: "Casts Programados",
        scheduled_empty_title: "No tienes casts programados",
        scheduled_empty_desc: "Genera un cast y programa su publicación para más tarde",
        scheduled_status_published: "Publicado",
        scheduled_status_scheduled: "Programado",
        scheduled_status_cancelled: "Cancelado",
        scheduled_status_failed: "Error",
        scheduled_topic: "Tema:",
        scheduled_error_loading: "Error obteniendo casts programados",
        scheduled_error_cancelling: "Error cancelando cast",
        scheduled_error_backend: "Backend no configurado. Verifica NEXT_PUBLIC_AGENT_SERVICE_URL",

        // Topics
        topic_tech: "Tech",
        topic_tech_desc: "Tecnología, blockchain, Web3",
        topic_musica: "Música",
        topic_musica_desc: "Música, artistas, canciones",
        topic_motivacion: "Motivación",
        topic_motivacion_desc: "Superación personal, crecimiento",
        topic_chistes: "Chistes",
        topic_chistes_desc: "Humor, memes, contenido divertido",
        topic_frases_celebres: "Frases Célebres",
        topic_frases_celebres_desc: "Citas inspiradoras",

        // Casts Page
        cast_page_connect_wallet: "Conecta tu wallet para generar y programar casts en Farcaster",
        cast_page_farcaster_required: "Necesitas estar autenticado con Farcaster para generar casts",
        cast_page_description: "Crea contenido viral para Farcaster. Paga 1 CELO y gana 100 XP por cada cast publicado.",
        cast_card_title: "Generar Casts con IA",
        cast_card_description: "Crea contenido viral para Farcaster. Paga 1 CELO y gana 100 XP",
        cast_tab_generate: "Generar",
        cast_tab_scheduled: "Programados",
    },
    en: {
        // Navbar
        nav_home: "Home",
        nav_guide: "Guide",
        nav_connect: "Connect",

        // Page
        hero_badge: "PUBLIC BETA",
        hero_title: "Viral Rewards on",
        hero_subtitle: "Farcaster",
        hero_description: "Viral Rewards on Farcaster",
        powered_by: "powered by",

        // Leaderboard
        trends_title: "Active Trends",
        trends_refresh: "Refresh Trends",
        trends_available_in: "Available in",
        trends_empty: "No recent trends.",
        trend_rank: "Trend",
        trend_by: "By",
        trend_join: "Join the trend",
        leaderboard_title: "Top Winners (24h)",
        leaderboard_empty: "No winners yet.",
        leaderboard_pending: "Pending",

        // Campaign Form
        form_action_placeholder: "Enter Farcaster cast link...",
        form_analyze_btn: "Analyze & Claim",
        form_analyzing: "Analyzing...",
        form_cooldown: "Return in",
        form_error_no_url: "Please enter a valid URL",
        form_status_scan: "Scanning...",
        form_status_analysis: "Analyzing...",
        form_status_verify: "Verifying...",
        form_status_send: "Sending...",
        form_status_done: "Done!",
        form_verify_btn: "Verify Requirements",
        form_recharge_btn: "Recharge Energy",
        form_energy_empty: "Out of Energy! 🔋",
        form_energy_desc: "You must wait for the next loot.",
        form_energy_ask: "Want to recharge instantly?",
        form_share_btn: "Share to Recharge",
        form_wait_btn: "Wait",

        // Reward Types
        reward_nft: "Loot NFT",
        reward_cusd: "MiniPay Drop",
        reward_xp: "XP Boost",

        // Analysis Overlay
        overlay_step1: "Analyzing cast...",
        overlay_step2: "Verifying eligibility...",
        overlay_step3: "Generating reward...",
        overlay_step4: "Finalizing transaction...",
        overlay_success: "Reward Claimed!",
        overlay_failed: "Not Eligible / Failed",
        overlay_view_tx: "View Transaction",
        overlay_close: "Close",

        // Settings
        settings_theme_light: "Light",
        settings_theme_dark: "Dark",
        settings_lang: "Language",

        // Cast Generator
        cast_select_topic: "Select a Topic",
        cast_select_topic_desc: "Choose the topic for your cast",
        cast_generate_title: "Generate Cast with AI",
        cast_generate_desc: "Use artificial intelligence to create viral content",
        cast_generating: "Generating...",
        cast_generate_btn: "Generate Cast",
        cast_generated: "Generated Cast",
        cast_characters: "characters",
        cast_schedule_title: "Schedule for later (Optional)",
        cast_schedule_will_publish: "Will be published on",
        cast_publish_btn: "Publish for 1 CELO",
        cast_confirming_payment: "Confirming payment...",
        cast_publishing: "Publishing...",
        cast_published_success: "Cast published successfully! You earned 100 XP",
        cast_success_note: "The cast was automatically published to your Farcaster profile using your approved signer.",
        cast_view_tx: "View transaction on CeloScan",
        cast_price: "Price: 1 CELO",
        cast_price_desc: "For each published cast you will receive",
        cast_price_xp: "100 XP",
        cast_price_reward: "as reward",
        cast_loading_address: "Loading agent address...",
        cast_error_backend: "Backend not configured. Check NEXT_PUBLIC_AGENT_SERVICE_URL",
        cast_error_generating: "Error generating cast",
        cast_error_publishing: "Error publishing cast",
        cast_error_payment: "Error initiating payment",
        cast_error_address: "Error getting agent address:",
        cast_error_signer_required: "A signer approval is required to publish casts. Please approve the signer in Warpcast and then return to this app.",
        cast_approval_url: "Approval URL",
        cast_approval_note: "Warpcast will open for you to approve the signer. After approving, return here to continue.",

        // Scheduled Casts
        scheduled_title: "Scheduled Casts",
        scheduled_empty_title: "You have no scheduled casts",
        scheduled_empty_desc: "Generate a cast and schedule its publication for later",
        scheduled_status_published: "Published",
        scheduled_status_scheduled: "Scheduled",
        scheduled_status_cancelled: "Cancelled",
        scheduled_status_failed: "Error",
        scheduled_topic: "Topic:",
        scheduled_error_loading: "Error getting scheduled casts",
        scheduled_error_cancelling: "Error cancelling cast",
        scheduled_error_backend: "Backend not configured. Check NEXT_PUBLIC_AGENT_SERVICE_URL",

        // Topics
        topic_tech: "Tech",
        topic_tech_desc: "Technology, blockchain, Web3",
        topic_musica: "Music",
        topic_musica_desc: "Music, artists, songs",
        topic_motivacion: "Motivation",
        topic_motivacion_desc: "Personal growth, self-improvement",
        topic_chistes: "Jokes",
        topic_chistes_desc: "Humor, memes, fun content",
        topic_frases_celebres: "Famous Quotes",
        topic_frases_celebres_desc: "Inspirational quotes",

        // Casts Page
        cast_page_connect_wallet: "Connect your wallet to generate and schedule casts on Farcaster",
        cast_page_farcaster_required: "You need to be authenticated with Farcaster to generate casts",
        cast_page_description: "Create viral content for Farcaster. Pay 1 CELO and earn 100 XP for each published cast.",
        cast_card_title: "Generate Casts with AI",
        cast_card_description: "Create viral content for Farcaster. Pay 1 CELO and earn 100 XP",
        cast_tab_generate: "Generate",
        cast_tab_scheduled: "Scheduled",
    }
} as const;

// Tipo para las claves del diccionario
export type DictionaryKey = keyof typeof dictionary.es;
