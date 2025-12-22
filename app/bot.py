import asyncio
import time
from datetime import datetime, timedelta
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from app.config import settings, logger
from app.network import get_network_state, calculate_heidelberg_score
from app.storage import DataManager

# --- 🧠 INTELLIGENT ALERT SYSTEM ---
ALERT_INTERVALS = {
    "OFFLINE": 600,       # 10 min - Critical: Node unreachable
    "CRITICAL": 3600,     # 1 hour - Severe issues requiring immediate action
    "WARNING": 21600,     # 6 hours - Performance optimization needed
    "DEFAULT": 3600       # 1 hour - Fallback for edge cases
}

# Global state management
db = DataManager(settings.HISTORY_FILE)
USER_IGNORES = db.get_ignores()
ALERT_HISTORY = {}
RECOVERY_NOTIFIED = {}
STRIKE_COUNT = {}

# --- 📊 HELPER FUNCTIONS ---

def format_uptime(seconds: float) -> str:
    """Convert seconds to human-readable uptime."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m"
    elif seconds < 86400:
        return f"{int(seconds/3600)}h {int((seconds % 3600)/60)}m"
    else:
        days = int(seconds/86400)
        hours = int((seconds % 86400)/3600)
        return f"{days}d {hours}h"

def format_storage(gb: float) -> str:
    """Format storage size with appropriate units."""
    if gb < 0.001:
        return f"{gb * 1024:.2f} MB"
    elif gb < 1:
        return f"{int(gb * 1000)} MB"
    else:
        return f"{gb:.2f} GB"

def get_health_emoji(score: int) -> str:
    """Return emoji based on health score."""
    if score >= 90:
        return "🟢"
    elif score >= 75:
        return "🟡"
    elif score >= 50:
        return "🟠"
    else:
        return "🔴"

def get_issue_tag(diagnosis_text: str) -> str:
    """Extract issue category from diagnosis text."""
    if "Version" in diagnosis_text or "Outdated" in diagnosis_text:
        return "VERSION"
    if "Storage" in diagnosis_text:
        return "STORAGE"
    if "Uptime" in diagnosis_text or "Restart" in diagnosis_text:
        return "UPTIME"
    if "Offline" in diagnosis_text or "Unreachable" in diagnosis_text:
        return "OFFLINE"
    return "GENERAL"

def get_severity_color(status: str) -> str:
    """Return color emoji for severity level."""
    return {
        "HEALTHY": "🟢",
        "WARNING": "🟡",
        "CRITICAL": "🔴",
        "OFFLINE": "⚫"
    }.get(status, "⚪")

# --- 🎯 CORE COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Enhanced /start command with smart onboarding.
    Handles: /start, /start <node_id>
    """
    args = context.args
    chat_id = str(update.effective_chat.id)
    
    # Case 1: No arguments - Show dashboard
    if not args:
        user_nodes = db.get_watchlist().get(chat_id, [])
        
        if user_nodes:
            # User has nodes - show dashboard
            status_msg = await update.message.reply_text("🔄 Loading your dashboard...")
            
            try:
                nodes, credits_map = await get_network_state()
                if nodes:
                    node_map = {n['pubkey']: n for n in nodes}
                    max_uptime = max([float(n.get('uptime', 0)) for n in nodes]) if nodes else 1
                    
                    status_lines = ["🎯 **YOUR NODE DASHBOARD**\n"]
                    
                    for idx, node_id in enumerate(user_nodes[:10], 1):  # Limit to 10 for readability
                        node = node_map.get(node_id)
                        
                        if not node:
                            status_lines.append(f"{idx}. ⚫ `{node_id}` **OFFLINE**")
                        else:
                            score_data = calculate_heidelberg_score(node, {"max_uptime": max_uptime})
                            score = score_data['total']
                            emoji = get_health_emoji(score)
                            version = node.get('version', 'Unknown')
                            uptime = format_uptime(float(node.get('uptime', 0)))
                            
                            status_lines.append(
                                f"{idx}. {emoji} `{node_id}` "
                                f"**{score}/100** • v{version} • ⏱️ {uptime}"
                            )
                    
                    if len(user_nodes) > 10:
                        status_lines.append(f"\n_...and {len(user_nodes) - 10} more_")
                    
                    status_lines.append(
                        f"\n📊 Use `/check` for detailed analysis"
                        f"\n🔔 Alerts are **ACTIVE** (checked every 5min)"
                        f"\n⚙️ Use `/help` for all commands"
                    )
                    
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                        text="\n".join(status_lines),
                        parse_mode='Markdown'
                    )
                else:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                        text="⚠️ Network temporarily unavailable. Your watchlist is safe."
                    )
            except Exception as e:
                logger.error(f"Dashboard load failed: {e}")
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text="❌ Failed to load dashboard. Use `/check` to retry."
                )
        else:
            # New user - onboarding
            welcome_msg = (
                "🛡️ **Welcome to Xandeum Sentinel**\n\n"
                "I'm your 24/7 node monitoring assistant. I'll watch your pNodes and alert you when:\n"
                "• 🔴 Node goes offline\n"
                "• ⚠️ Health score drops\n"
                "• 📉 Performance degrades\n"
                "• 🔄 Version becomes outdated\n\n"
                "**Quick Start:**\n"
                "1️⃣ Get your node's public key\n"
                "2️⃣ Send me: `/watch YOUR_NODE_ID`\n"
                "3️⃣ I'll scan it and start monitoring\n\n"
                "**Example:**\n"
                "`/watch 5xHn7K2mPxQ...`\n\n"
                "📚 Type `/help` to see all commands"
            )
            await update.message.reply_text(welcome_msg, parse_mode='Markdown')
        return

    # Case 2: Node ID provided - Add to watchlist
    node_id = args[0].strip()
    
    # Validation
    if len(node_id) < 32:
        await update.message.reply_text(
            "⚠️ **Invalid Node ID**\n\n"
            "Node IDs should be at least 32 characters.\n"
            "Example: `5xHn7K2mPxQ9vK8...`\n\n"
            "💡 Tip: Copy the full pubkey from your node or the dashboard.",
            parse_mode='Markdown'
        )
        return
    
    # Check if already watching
    if db.add_watch(chat_id, node_id):
        await update.message.reply_text(
            f"✅ **Monitoring Activated**\n\n"
            f"Node: `{node_id}`\n\n"
            f"🔄 Running initial health scan...",
            parse_mode='Markdown'
        )
        
        # Initial health check
        await perform_initial_scan(update, context, chat_id, node_id)
    else:
        await update.message.reply_text(
            f"ℹ️ **Already Monitoring**\n\n"
            f"You're already watching this node.\n"
            f"Use `/check {node_id}` to see its status.",
            parse_mode='Markdown'
        )

async def perform_initial_scan(update, context, chat_id: str, node_id: str):
    """Perform detailed initial scan when user adds a node."""
    try:
        nodes, credits_map = await get_network_state()
        target_node = next((n for n in nodes if n['pubkey'] == node_id), None)
        
        if not target_node:
            # Node is offline during initial scan
            await context.bot.send_message(
                chat_id,
                f"⚫ **Initial Scan: Node Offline**\n\n"
                f"Node `{node_id}` is currently unreachable.\n\n"
                f"**This could mean:**\n"
                f"• Node is starting up\n"
                f"• Temporary network issue\n"
                f"• Node is actually offline\n\n"
                f"🔔 I'll alert you when it comes online.\n"
                f"🔄 Check manually: `/check {node_id}`",
                parse_mode='Markdown'
            )
            
            # Set alert history to prevent immediate spam
            alert_key = f"{chat_id}_{node_id}_OFFLINE"
            ALERT_HISTORY[alert_key] = time.time()
        else:
            # Node is online - show detailed report
            max_uptime = max([float(n.get('uptime', 0)) for n in nodes]) if nodes else 1
            score_data = calculate_heidelberg_score(target_node, {"max_uptime": max_uptime})
            report = diagnose_node(target_node, max_uptime)
            
            # Get official credits
            official_credits = credits_map.get(node_id, 0)
            
            # Build comprehensive report
            score = score_data['total']
            emoji = get_health_emoji(score)
            version = target_node.get('version', 'Unknown')
            uptime = format_uptime(float(target_node.get('uptime', 0)))
            storage_gb = float(target_node.get('storage_committed', 0)) / (1024**3)
            storage_str = format_storage(storage_gb)
            latency = target_node.get('_reporting_latency', 0)
            
            report_lines = [
                f"{emoji} **Initial Health Scan Complete**\n",
                f"**Node ID:** `{node_id}`",
                f"**Health Score:** {score}/100",
                f"**Status:** {report['status']}\n",
                f"📊 **Metrics:**",
                f"• Version: `{version}`",
                f"• Uptime: `{uptime}`",
                f"• Storage: `{storage_str}`",
                f"• Latency: `{latency:.0f}ms`",
                f"• Credits: `{official_credits}`\n",
            ]
            
            # Add score breakdown
            breakdown = score_data['breakdown']
            report_lines.append(f"🎯 **Score Breakdown:**")
            report_lines.append(f"• Version: {breakdown['v0.7_compliance']}/40")
            report_lines.append(f"• Uptime: {breakdown['uptime_reliability']}/30")
            report_lines.append(f"• Storage: {breakdown['storage_weight']}/20")
            report_lines.append(f"• Paging: {breakdown['paging_efficiency']}/10\n")
            
            # Add diagnosis if any issues
            if report['status'] != "HEALTHY":
                report_lines.append(f"⚠️ **Issues Detected:**")
                report_lines.append(report['diagnosis'])
                report_lines.append(f"\n💡 **Recommended Actions:**")
                report_lines.append(report['action'])
            else:
                report_lines.append(f"✨ **Excellent!** No issues detected.")
                report_lines.append(f"Your node is performing optimally.")
            
            report_lines.append(f"\n🔔 You'll receive alerts if status changes.")
            
            await context.bot.send_message(
                chat_id,
                "\n".join(report_lines),
                parse_mode='Markdown'
            )
            
            # If there are issues, set alert history to prevent immediate re-alert
            if report['status'] != "HEALTHY":
                issue_tag = get_issue_tag(report['diagnosis'])
                history_key = f"{chat_id}_{node_id}_{issue_tag}"
                ALERT_HISTORY[history_key] = time.time()
                
    except Exception as e:
        logger.error(f"Initial scan failed: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id,
            f"❌ **Scan Failed**\n\n"
            f"Could not complete initial scan due to a technical error.\n"
            f"Don't worry - monitoring is still active.\n\n"
            f"Try manually: `/check {node_id}`",
            parse_mode='Markdown'
        )

async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for /start with node ID."""
    await start(update, context)

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Enhanced /check command with detailed analysis.
    Supports: /check (all nodes), /check <node_id> (specific node)
    """
    chat_id = str(update.effective_chat.id)
    args = context.args
    
    # Determine what to check
    nodes_to_check = []
    check_all = False
    
    if args:
        # Specific node requested
        node_query = args[0].strip()
        
        # Check if it's a partial ID or full ID
        user_watchlist = db.get_watchlist().get(chat_id, [])
        matching_nodes = [n for n in user_watchlist if n.startswith(node_query) or node_query in n]
        
        if matching_nodes:
            nodes_to_check = matching_nodes
        else:
            # Maybe they provided a full ID not in watchlist
            nodes_to_check = [node_query]
    else:
        # Check all watched nodes
        nodes_to_check = db.get_watchlist().get(chat_id, [])
        check_all = True

    if not nodes_to_check:
        await update.message.reply_text(
            "🤷 **No Nodes to Check**\n\n"
            "You're not watching any nodes yet.\n"
            "Add one with: `/watch YOUR_NODE_ID`\n\n"
            "💡 Or check any node: `/check <node_id>`",
            parse_mode='Markdown'
        )
        return

    # Show scanning message
    status_msg = await update.message.reply_text(
        f"🔍 **Scanning {len(nodes_to_check)} node{'s' if len(nodes_to_check) > 1 else ''}...**\n"
        f"_This may take a few seconds_",
        parse_mode='Markdown'
    )
    
    try:
        # Fetch fresh network state
        nodes, credits_map = await get_network_state()
        
        if not nodes:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text="⚠️ **Network Unavailable**\n\n"
                     "Could not reach Xandeum network. Please try again in a moment.",
                parse_mode='Markdown'
            )
            return

        node_map = {n['pubkey']: n for n in nodes}
        max_uptime = max([float(n.get('uptime', 0)) for n in nodes]) if nodes else 1
        
        # Build report
        if check_all and len(nodes_to_check) > 1:
            # Summary view for multiple nodes
            await generate_summary_report(context, chat_id, status_msg.message_id, nodes_to_check, node_map, max_uptime, credits_map, nodes)
        else:
            # Detailed view for single node
            await generate_detailed_report(context, chat_id, status_msg.message_id, nodes_to_check[0], node_map, max_uptime, credits_map, nodes)
        
    except Exception as e:
        logger.error(f"Check command failed: {e}", exc_info=True)
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text="❌ **Scan Failed**\n\n"
                 "A technical error occurred. Please try again.\n"
                 f"Error: `{str(e)[:100]}`",
            parse_mode='Markdown'
        )

async def generate_summary_report(context, chat_id, message_id, node_ids, node_map, max_uptime, credits_map, all_nodes):
    """Generate summary report for multiple nodes."""
    report_lines = ["📊 **HEALTH STATUS REPORT**\n"]
    
    healthy_count = 0
    warning_count = 0
    critical_count = 0
    offline_count = 0
    
    node_details = []
    
    for idx, node_id in enumerate(node_ids[:20], 1):  # Limit to 20 for message size
        node = node_map.get(node_id)
        
        if not node:
            offline_count += 1
            node_details.append(
                f"{idx}. ⚫ `{node_id}` **OFFLINE**"
            )
        else:
            score_data = calculate_heidelberg_score(node, {"max_uptime": max_uptime})
            score = score_data['total']
            report = diagnose_node(node, max_uptime)
            emoji = get_health_emoji(score)
            version = node.get('version', '?')
            uptime = format_uptime(float(node.get('uptime', 0)))
            
            # Count by status
            if report['status'] == "HEALTHY":
                healthy_count += 1
            elif report['status'] == "WARNING":
                warning_count += 1
            elif report['status'] == "CRITICAL":
                critical_count += 1
            
            status_emoji = get_severity_color(report['status'])
            
            node_details.append(
                f"{idx}. {emoji} `{node_id}` "
                f"**{score}/100** {status_emoji}\n"
                f"   ↳ v{version} • {uptime}"
            )
    
    # Summary stats
    total = len(node_ids)
    report_lines.append(
        f"📈 **Summary:** {total} node{'s' if total > 1 else ''}\n"
        f"🟢 Healthy: {healthy_count} • "
        f"🟡 Warning: {warning_count}\n"
        f"🔴 Critical: {critical_count} • "
        f"⚫ Offline: {offline_count}\n"
    )
    
    # Network comparison
    avg_network_health = sum(
        calculate_heidelberg_score(n, {"max_uptime": max_uptime})['total'] 
        for n in all_nodes
    ) / len(all_nodes) if all_nodes else 0
    
    your_avg = sum(
        calculate_heidelberg_score(node_map[nid], {"max_uptime": max_uptime})['total']
        for nid in node_ids if nid in node_map
    ) / len([nid for nid in node_ids if nid in node_map]) if any(nid in node_map for nid in node_ids) else 0
    
    if your_avg > 0:
        comparison = "above" if your_avg >= avg_network_health else "below"
        diff = abs(your_avg - avg_network_health)
        report_lines.append(
            f"🎯 **Your Avg:** {your_avg:.1f}/100\n"
            f"📊 **Network Avg:** {avg_network_health:.1f}/100\n"
            f"📍 You're **{diff:.1f} pts {comparison}** network average\n"
        )
    
    # Node details
    report_lines.append("**Nodes:**")
    report_lines.extend(node_details)
    
    if len(node_ids) > 20:
        report_lines.append(f"\n_...and {len(node_ids) - 20} more_")
    
    report_lines.append(
        f"\n💡 **Tip:** Check individual nodes with:\n"
        f"`/check <node_id>`"
    )
    
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text="\n".join(report_lines),
        parse_mode='Markdown'
    )

async def generate_detailed_report(context, chat_id, message_id, node_id, node_map, max_uptime, credits_map, all_nodes):
    """Generate detailed report for single node."""
    node = node_map.get(node_id)
    
    if not node:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"⚫ **Node Status: OFFLINE**\n\n"
                 f"**ID:** `{node_id}`\n\n"
                 f"This node is currently unreachable.\n\n"
                 f"**Possible reasons:**\n"
                 f"• Node stopped/crashed\n"
                 f"• Network connectivity issue\n"
                 f"• Maintenance in progress\n\n"
                 f"🔄 Try again: `/check {node_id}`\n"
                 f"🔔 You'll be alerted when it comes back online.",
            parse_mode='Markdown'
        )
        return
    
    # Calculate metrics
    score_data = calculate_heidelberg_score(node, {"max_uptime": max_uptime})
    report = diagnose_node(node, max_uptime)
    
    score = score_data['total']
    emoji = get_health_emoji(score)
    status_emoji = get_severity_color(report['status'])
    version = node.get('version', 'Unknown')
    uptime = format_uptime(float(node.get('uptime', 0)))
    uptime_sec = float(node.get('uptime', 0))
    storage_gb = float(node.get('storage_committed', 0)) / (1024**3)
    storage_str = format_storage(storage_gb)
    storage_used = float(node.get('storage_used', 0)) / (1024**3)
    storage_used_str = format_storage(storage_used)
    latency = node.get('_reporting_latency', 0)
    hit_rate = float(node.get('paging_hit_rate', 0))
    official_credits = credits_map.get(node_id, 0)
    
    # Network ranking
    all_scores = [calculate_heidelberg_score(n, {"max_uptime": max_uptime})['total'] for n in all_nodes]
    all_scores.sort(reverse=True)
    rank = all_scores.index(score) + 1 if score in all_scores else "N/A"
    percentile = ((len(all_scores) - rank) / len(all_scores) * 100) if isinstance(rank, int) else 0
    
    # Build detailed report
    report_lines = [
        f"{emoji} **DETAILED NODE ANALYSIS** {status_emoji}\n",
        f"**Node ID:** `{node_id}`",
        f"**Overall Score:** {score}/100",
        f"**Status:** {report['status']}",
        f"**Network Rank:** #{rank} of {len(all_nodes)} (Top {100-percentile:.0f}%)\n",
        
        f"📊 **Performance Metrics:**",
        f"• Version: `{version}`",
        f"• Uptime: `{uptime}` ({uptime_sec:,.0f}s)",
        f"• Storage Committed: `{storage_str}`",
        f"• Storage Used: `{storage_used_str}`",
        f"• Paging Hit Rate: `{hit_rate*100:.1f}%`",
        f"• Response Latency: `{latency:.0f}ms`",
        f"• Reputation Credits: `{official_credits:,}`\n",
        
        f"🎯 **Score Breakdown:**",
    ]
    
    breakdown = score_data['breakdown']
    report_lines.append(f"```")
    report_lines.append(f"Version:  {breakdown['v0.7_compliance']:2d}/40 {'█'*int(breakdown['v0.7_compliance']/4)}")
    report_lines.append(f"Uptime:   {breakdown['uptime_reliability']:2d}/30 {'█'*int(breakdown['uptime_reliability']/3)}")
    report_lines.append(f"Storage:  {breakdown['storage_weight']:2d}/20 {'█'*int(breakdown['storage_weight']/2)}")
    report_lines.append(f"Paging:   {breakdown['paging_efficiency']:2d}/10 {'█'*breakdown['paging_efficiency']}")
    report_lines.append(f"```")
    
    # Add diagnosis
    if report['status'] != "HEALTHY":
        report_lines.append(f"\n⚠️ **Issues Detected:**")
        report_lines.append(report['diagnosis'])
        report_lines.append(f"\n🛠️ **Recommended Actions:**")
        report_lines.append(report['action'])
    else:
        report_lines.append(f"\n✅ **All Systems Optimal**")
        report_lines.append(f"No issues detected. Keep up the great work!")
    
    # Add action buttons
    issue_tag = get_issue_tag(report['diagnosis']) if report['status'] != "HEALTHY" else "GENERAL"
    keyboard = []
    
    if report['status'] != "HEALTHY":
        keyboard.append([
            InlineKeyboardButton("🔄 Re-scan Now", callback_data=f"RESCAN|{node_id}|{issue_tag}"),
            InlineKeyboardButton("✅ Acknowledge", callback_data=f"OK|{node_id}|{issue_tag}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔄 Refresh", callback_data=f"REFRESH|{node_id}"),
        InlineKeyboardButton("🗑️ Stop Watching", callback_data=f"UNWATCH|{node_id}")
    ])
    
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text="\n".join(report_lines),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all watched nodes with quick status."""
    chat_id = str(update.effective_chat.id)
    user_nodes = db.get_watchlist().get(chat_id, [])
    
    if not user_nodes:
        await update.message.reply_text(
            "📭 **Watchlist Empty**\n\n"
            "You're not monitoring any nodes yet.\n\n"
            "**Get Started:**\n"
            "`/watch YOUR_NODE_ID`\n\n"
            "💡 You can monitor multiple nodes simultaneously!",
            parse_mode='Markdown'
        )
        return
    
    # Show list with inline buttons
    keyboard = []
    for node_id in user_nodes[:15]:  # Limit to 15 for button constraints
        btn_label = f"📊 {node_id[:6]}...{node_id[-4:]}"
        keyboard.append([
            InlineKeyboardButton(btn_label, callback_data=f"DETAIL|{node_id}"),
            InlineKeyboardButton("❌", callback_data=f"UNWATCH|{node_id}")
        ])
    
    msg = (
        f"📋 **Your Watchlist** ({len(user_nodes)} node{'s' if len(user_nodes) != 1 else ''})\n\n"
        f"Tap any node for detailed status:\n\n"
    )
    
    if len(user_nodes) > 15:
        msg += f"_Showing first 15 of {len(user_nodes)} nodes_\n"
    
    msg += f"\n🔄 Full Status: `/check`\n💡 Add More: `/watch <id>`"
    
    await update.message.reply_text(
        msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def unwatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Enhanced /unwatch with confirmation and statistics.
    Supports: /unwatch (interactive), /unwatch <node_id> (direct)
    """
    query = update.callback_query
    chat_id = str(update.effective_chat.id)
    
    # Handle callback from buttons
    if query:
        await query.answer()
        node_id = query.data.split("|")[1]
        
        if db.remove_watch(chat_id, node_id):
            # Clear any ignores for this node
            ignores_to_remove = [k for k in USER_IGNORES.keys() if f"{chat_id}_{node_id}" in k]
            for k in ignores_to_remove:
                del USER_IGNORES[k]
            db.save_ignores(USER_IGNORES)
            
            await query.edit_message_text(
                f"🗑️ **Monitoring Stopped**\n\n"
                f"Node: `{node_id}`\n\n"
                f"✅ Watchlist updated\n"
                f"✅ Alert history cleared\n"
                f"✅ Preferences reset\n\n"
                f"Want to monitor it again? `/watch {node_id}`",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"⚠️ **Error**\n\nCould not remove node from watchlist.",
                parse_mode='Markdown'
            )
        return
    
    # Handle command
    args = context.args
    
    if not args:
        # Show interactive list
        user_nodes = db.get_watchlist().get(chat_id, [])
        
        if not user_nodes:
            await update.message.reply_text(
                "🤷 **Nothing to Remove**\n\n"
                "Your watchlist is already empty.",
                parse_mode='Markdown'
            )
            return
        
        keyboard = []
        for node_id in user_nodes:
            btn_label = f"❌ {node_id[:8]}...{node_id[-6:]}"
            keyboard.append([InlineKeyboardButton(btn_label, callback_data=f"UNWATCH|{node_id}")])
        
        await update.message.reply_text(
            f"🛑 **Remove from Watchlist**\n\n"
            f"You're watching {len(user_nodes)} node{'s' if len(user_nodes) != 1 else ''}.\n"
            f"Tap any node to stop monitoring:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Direct removal with node ID
    node_id = args[0].strip()
    user_nodes = db.get_watchlist().get(chat_id, [])
    
    # Find matching node (support partial IDs)
    matching = [n for n in user_nodes if n.startswith(node_id) or node_id in n]
    
    if not matching:
        await update.message.reply_text(
            f"⚠️ **Node Not Found**\n\n"
            f"`{node_id}` is not in your watchlist.\n\n"
            f"📋 View all: `/list`",
            parse_mode='Markdown'
        )
        return
    
    if len(matching) > 1:
        await update.message.reply_text(
            f"⚠️ **Multiple Matches**\n\n"
            f"Found {len(matching)} nodes matching `{node_id}`.\n"
            f"Please provide more characters.\n\n"
            f"📋 View all: `/list`",
            parse_mode='Markdown'
        )
        return
    
    # Remove the node
    node_to_remove = matching[0]
    if db.remove_watch(chat_id, node_to_remove):
        # Cleanup
        ignores_to_remove = [k for k in USER_IGNORES.keys() if f"{chat_id}_{node_to_remove}" in k]
        for k in ignores_to_remove:
            del USER_IGNORES[k]
        db.save_ignores(USER_IGNORES)
        
        await update.message.reply_text(
            f"🗑️ **Monitoring Stopped**\n\n"
            f"Node: `{node_to_remove}`\n\n"
            f"All alerts and preferences cleared.\n\n"
            f"💚 Thanks for using Sentinel!",
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comprehensive help with examples and tips."""
    help_text = (
        "🛡️ **XANDEUM SENTINEL - COMMAND GUIDE**\n\n"
        
        "**📊 Monitoring Commands:**\n"
        "`/start` - Dashboard & welcome\n"
        "`/watch <node_id>` - Start monitoring a node\n"
        "`/check` - Check all watched nodes\n"
        "`/check <node_id>` - Check specific node\n"
        "`/list` - View your watchlist\n"
        "`/stop` or `/unwatch` - Stop monitoring\n\n"
        
        "**⚙️ Management:**\n"
        "• Snooze alerts (24h) via message buttons\n"
        "• Ignore specific issues permanently\n"
        "• Re-scan nodes on demand\n"
        "• Instant recovery notifications\n\n"
        
        "**🔔 Alert System:**\n"
        "• 🔴 CRITICAL → Alert every 1 hour\n"
        "• 🟡 WARNING → Alert every 6 hours\n"
        "• ⚫ OFFLINE → Alert every 10 minutes\n"
        "• 🟢 RECOVERY → Immediate notification\n\n"
        
        "**💡 Pro Tips:**\n"
        "• Monitor multiple nodes simultaneously\n"
        "• Use partial IDs in commands (e.g., `/check 5xHn7`)\n"
        "• Snooze during planned maintenance\n"
        "• Compare your nodes to network average\n\n"
        
        "**📚 Examples:**\n"
        "`/watch 5xHn7K2mPxQ9vK8...`\n"
        "`/check 5xHn7` (partial ID works!)\n"
        "`/stop 5xHn7`\n\n"
        
        "**❓ Need Help?**\n"
        "• Check [Documentation](https://docs.xandeum.network)\n"
        "• Join [Community](https://discord.com/invite/uqRSmmM5m)\n\n"
        
        "Made with ❤️ for Xandeum Network"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show network-wide statistics."""
    status_msg = await update.message.reply_text("📊 Gathering network statistics...")
    
    try:
        nodes, credits_map = await get_network_state()
        
        if not nodes:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
                text="⚠️ Could not fetch network data. Try again in a moment."
            )
            return
        
        max_uptime = max([float(n.get('uptime', 0)) for n in nodes])
        
        # Calculate statistics
        total_nodes = len(nodes)
        scores = [calculate_heidelberg_score(n, {"max_uptime": max_uptime})['total'] for n in nodes]
        avg_score = sum(scores) / len(scores)
        
        versions = {}
        for n in nodes:
            v = str(n.get('version', 'Unknown'))
            versions[v] = versions.get(v, 0) + 1
        
        total_storage = sum(float(n.get('storage_committed', 0)) for n in nodes) / (1024**3)
        total_credits = sum(credits_map.values())
        
        healthy = sum(1 for s in scores if s >= 90)
        good = sum(1 for s in scores if 75 <= s < 90)
        fair = sum(1 for s in scores if 50 <= s < 75)
        poor = sum(1 for s in scores if s < 50)
        
        # Build report
        report = (
            "🌐 **NETWORK STATISTICS**\n\n"
            
            f"📊 **Overview:**\n"
            f"• Total Nodes: `{total_nodes:,}`\n"
            f"• Avg Health: `{avg_score:.1f}/100`\n"
            f"• Total Storage: `{total_storage:.2f} GB`\n"
            f"• Total Credits: `{total_credits:,}`\n\n"
            
            f"🎯 **Health Distribution:**\n"
            f"• 🟢 Excellent (90+): {healthy} ({healthy/total_nodes*100:.1f}%)\n"
            f"• 🟡 Good (75-89): {good} ({good/total_nodes*100:.1f}%)\n"
            f"• 🟠 Fair (50-74): {fair} ({fair/total_nodes*100:.1f}%)\n"
            f"• 🔴 Poor (<50): {poor} ({poor/total_nodes*100:.1f}%)\n\n"
            
            f"📦 **Version Distribution:**\n"
        )
        
        # Show top 5 versions
        top_versions = sorted(versions.items(), key=lambda x: x[1], reverse=True)[:5]
        for v, count in top_versions:
            percentage = count / total_nodes * 100
            report += f"• `{v}`: {count} ({percentage:.1f}%)\n"
        
        report += (
            f"\n💡 **Your Status:**\n"
            f"Watching: {len(db.get_watchlist().get(str(update.effective_chat.id), []))} nodes\n"
            f"Use `/check` to see how you compare!"
        )
        
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=report,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Stats command failed: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text="❌ Failed to generate statistics. Please try again."
        )

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows users to just paste a Node ID without typing /watch."""
    text = update.message.text.strip()
    if len(text) >= 32:
        context.args = [text]
        await watch_command(update, context)
    else:
        await update.message.reply_text("❓ Use `/watch <id>` or send a valid Node ID.")
        
# --- 🔔 BACKGROUND WATCHDOG ---

async def check_nodes(context: ContextTypes.DEFAULT_TYPE):
    """
    Enhanced background watchdog with smart alerting and recovery detection.
    Runs every 5 minutes.
    """
    watchlist = db.get_watchlist()
    if not watchlist:
        return

    try:
        nodes, credits_map = await get_network_state()
        
        # Safety check
        if not nodes or len(nodes) < 10:
            logger.warning(f"Suspiciously low node count: {len(nodes) if nodes else 0}. Skipping alert cycle.")
            return

        node_map = {n['pubkey']: n for n in nodes}
        max_uptime = max([float(n.get('uptime', 0)) for n in nodes]) if nodes else 1

        for chat_id, watched_ids in watchlist.items():
            for pubkey in watched_ids:
                node = node_map.get(pubkey)
                strike_key = f"{chat_id}_{pubkey}_OFFLINE"
                
                # --- CASE 1: NODE APPEARS OFFLINE ---
                if not node:
                    # Increment Strike Count
                    current_strikes = STRIKE_COUNT.get(strike_key, 0) + 1
                    STRIKE_COUNT[strike_key] = current_strikes
                    
                    # ONLY alert if failures >= 2 (10 minutes confirmed downtime)
                    if current_strikes >= 2:
                        await handle_offline_alert(context, chat_id, pubkey)
                    else:
                        logger.info(f"Node {pubkey[:8]} missed check 1. Strikes: {current_strikes}/2")
                    continue

                # --- CASE 2: NODE IS ONLINE (Recovery) ---
                else:
                    # Reset strikes immediately if it's back online
                    if strike_key in STRIKE_COUNT:
                        del STRIKE_COUNT[strike_key]

                # --- CASE 3: HEALTH ISSUES ---
                report = diagnose_node(node, max_uptime)
                
                if report['status'] != "HEALTHY":
                    await handle_health_alert(context, chat_id, pubkey, node, report, max_uptime)
                else:
                    # Node is healthy - check if we need to send recovery notification
                    await handle_recovery_from_issues(context, chat_id, pubkey, node, max_uptime)
                            
    except Exception as e:
        logger.error(f"Watchdog loop error: {e}", exc_info=True)

async def handle_offline_alert(context, chat_id: str, pubkey: str):
    """Handle offline node alerts with rate limiting."""
    alert_key = f"{chat_id}_{pubkey}_OFFLINE"
    last_alert = ALERT_HISTORY.get(alert_key, 0)
    
    if (time.time() - last_alert) > ALERT_INTERVALS["OFFLINE"]:
        try:
            offline_duration = int((time.time() - last_alert) / 60) if last_alert > 0 else 0
            
            keyboard = [[
                InlineKeyboardButton("🔄 Check Now", callback_data=f"RESCAN|{pubkey}|OFFLINE"),
                InlineKeyboardButton("✅ Acknowledge", callback_data=f"OK|{pubkey}|OFFLINE")
            ]]
            
            msg = (
                f"⚫ **NODE OFFLINE ALERT**\n\n"
                f"**Node ID:** `{pubkey}`\n"
                f"**Status:** Unreachable\n"
            )
            
            if offline_duration > 0:
                msg += f"**Duration:** {offline_duration} minutes\n"
            
            msg += (
                f"\n**Possible causes:**\n"
                f"• Node process stopped\n"
                f"• Network connectivity lost\n"
                f"• Server maintenance\n"
                f"• Configuration error\n\n"
                f"🔔 _Next alert in 10 minutes_"
            )
            
            await context.bot.send_message(
                chat_id,
                msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            ALERT_HISTORY[alert_key] = time.time()
        except Exception as e:
            logger.error(f"Failed to send offline alert: {e}")

async def handle_health_alert(context, chat_id: str, pubkey: str, node: dict, report: dict, max_uptime: float):
    """Handle health issue alerts with smart rate limiting."""
    issue_tag = get_issue_tag(report['diagnosis'])
    
    # Check if user has ignored this issue
    ignore_key = f"{chat_id}_{pubkey}_{issue_tag}"
    if time.time() < USER_IGNORES.get(ignore_key, 0):
        return
    
    # Determine cooldown based on severity
    severity = report['status']
    cooldown = ALERT_INTERVALS.get(severity, ALERT_INTERVALS["DEFAULT"])
    
    history_key = f"{chat_id}_{pubkey}_{issue_tag}"
    last_alert = ALERT_HISTORY.get(history_key, 0)
    
    if (time.time() - last_alert) > cooldown:
        await send_alert_with_buttons(context, chat_id, pubkey, report, node, max_uptime)
        ALERT_HISTORY[history_key] = time.time()

async def handle_recovery_from_issues(context, chat_id: str, pubkey: str, node: dict, max_uptime: float):
    """Send recovery notification when node returns to healthy state."""
    # Check if we had any active alerts for this node
    possible_issues = ["VERSION", "STORAGE", "UPTIME", "GENERAL"]
    
    for issue in possible_issues:
        history_key = f"{chat_id}_{pubkey}_{issue}"
        recovery_key = f"{chat_id}_{pubkey}_RECOVERY_{issue}"
        
        if history_key in ALERT_HISTORY and recovery_key not in RECOVERY_NOTIFIED:
            # Node recovered from this issue
            await send_recovery_notification(context, chat_id, pubkey, node, max_uptime, issue)
            RECOVERY_NOTIFIED[recovery_key] = time.time()
            del ALERT_HISTORY[history_key]

async def send_recovery_notification(context, chat_id: str, pubkey: str, node: dict, max_uptime: float, issue: str = "OFFLINE"):
    """Send recovery notification."""
    try:
        score_data = calculate_heidelberg_score(node, {"max_uptime": max_uptime})
        score = score_data['total']
        emoji = get_health_emoji(score)
        
        version = node.get('version', 'Unknown')
        uptime = format_uptime(float(node.get('uptime', 0)))
        
        msg = (
            f"🎉 **RECOVERY NOTIFICATION**\n\n"
            f"**Node ID:** `{pubkey}`\n"
            f"**Status:** {emoji} Back to Healthy!\n"
            f"**Health Score:** {score}/100\n\n"
            f"📊 **Current Metrics:**\n"
            f"• Version: `{version}`\n"
            f"• Uptime: `{uptime}`\n\n"
        )
        
        if issue == "OFFLINE":
            msg += "✅ Node is back online and responding to queries."
        else:
            msg += f"✅ The **{issue}** issue has been resolved."
        
        msg += "\n\n💚 Great job fixing it!"
        
        await context.bot.send_message(
            chat_id,
            msg,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send recovery notification: {e}")

async def send_alert_with_buttons(context, chat_id: str, pubkey: str, report: dict, node: dict, max_uptime: float):
    """Send alert with enhanced information and action buttons."""
    issue_tag = get_issue_tag(report['diagnosis'])
    
    score_data = calculate_heidelberg_score(node, {"max_uptime": max_uptime})
    score = score_data['total']
    emoji = get_health_emoji(score)
    
    version = node.get('version', 'Unknown')
    uptime = format_uptime(float(node.get('uptime', 0)))
    
    # Build keyboard
    keyboard = [
        [
            InlineKeyboardButton("🔄 Re-scan", callback_data=f"RESCAN|{pubkey}|{issue_tag}"),
            InlineKeyboardButton("✅ Got it", callback_data=f"OK|{pubkey}|{issue_tag}")
        ],
        [
            InlineKeyboardButton("💤 Snooze 24h", callback_data=f"SZ|{pubkey}|{issue_tag}"),
            InlineKeyboardButton("🔇 Ignore Forever", callback_data=f"IG|{pubkey}|{issue_tag}")
        ]
    ]
    
    # Determine visual style
    if report['status'] == "CRITICAL":
        color = "🔴"
        title = "CRITICAL ALERT"
        urgency = "⚠️ **IMMEDIATE ACTION REQUIRED**"
    else:
        color = "🟡"
        title = "PERFORMANCE WARNING"
        urgency = "💡 **Optimization Recommended**"
    
    try:
        msg = (
            f"{color} **{title}**\n"
            f"{urgency}\n\n"
            f"**Node ID:** `{pubkey}`\n"
            f"**Health Score:** {emoji} {score}/100\n"
            f"**Current Version:** `{version}`\n"
            f"**Uptime:** `{uptime}`\n\n"
            f"🔍 **Issues Found:**\n{report['diagnosis']}\n\n"
            f"🛠️ **Recommended Actions:**\n{report['action']}\n\n"
            f"🔔 _Next alert: {ALERT_INTERVALS[report['status']]//3600}h_ • `/check {pubkey}` for details"
        )
        
        await context.bot.send_message(
            chat_id,
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")

# --- 🎮 BUTTON HANDLERS ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced button handler with all interactions."""
    query = update.callback_query
    data = query.data.split("|")
    action = data[0]

    # UNWATCH button
    if action == "UNWATCH":
        await unwatch_command(update, context)
        return
    
    # DETAIL button (from /list)
    if action == "DETAIL":
        pubkey = data[1]
        chat_id = str(update.effective_chat.id)
        
        await query.answer("🔄 Loading details...")
        
        try:
            nodes, credits_map = await get_network_state()
            node_map = {n['pubkey']: n for n in nodes}
            max_uptime = max([float(n.get('uptime', 0)) for n in nodes]) if nodes else 1
            
            # Generate detailed report for this node
            await generate_detailed_report(
                context, 
                chat_id, 
                query.message.message_id, 
                pubkey, 
                node_map, 
                max_uptime, 
                credits_map, 
                nodes
            )
        except Exception as e:
            logger.error(f"Detail view failed: {e}")
            await query.answer("❌ Failed to load details", show_alert=True)
        return
    
    # REFRESH button
    if action == "REFRESH":
        pubkey = data[1]
        chat_id = str(update.effective_chat.id)
        
        await query.answer("🔄 Refreshing...")
        
        try:
            nodes, credits_map = await get_network_state()
            node_map = {n['pubkey']: n for n in nodes}
            max_uptime = max([float(n.get('uptime', 0)) for n in nodes]) if nodes else 1
            
            await generate_detailed_report(
                context,
                chat_id,
                query.message.message_id,
                pubkey,
                node_map,
                max_uptime,
                credits_map,
                nodes
            )
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            await query.answer("❌ Refresh failed", show_alert=True)
        return

    # RESCAN button
    if action == "RESCAN":
        pubkey = data[1]
        issue_type = data[2]
        
        await query.answer("🔄 Scanning...", show_alert=False)
        
        try:
            nodes, credits_map = await get_network_state()
            target = next((n for n in nodes if n['pubkey'] == pubkey), None)
            
            if not target:
                await query.answer("⚫ Node still OFFLINE", show_alert=True)
                return
            
            max_uptime = max([float(n.get('uptime', 0)) for n in nodes]) if nodes else 1
            report = diagnose_node(target, max_uptime)
            score_data = calculate_heidelberg_score(target, {"max_uptime": max_uptime})
            score = score_data['total']
            
            if report['status'] == "HEALTHY":
                emoji = get_health_emoji(score)
                await query.edit_message_text(
                    f"✅ **ISSUE RESOLVED!**\n\n"
                    f"Node `{pubkey}` is now {emoji} **HEALTHY**\n"
                    f"Health Score: **{score}/100**\n\n"
                    f"🎉 Great work resolving the issue!",
                    parse_mode='Markdown'
                )
                # Clear alert history for this issue
                history_key = f"{query.message.chat.id}_{pubkey}_{issue_type}"
                if history_key in ALERT_HISTORY:
                    del ALERT_HISTORY[history_key]
            else:
                current_issue = get_issue_tag(report['diagnosis'])
                if current_issue == issue_type:
                    await query.answer(f"❌ Issue persists: {report['status']}", show_alert=True)
                else:
                    await query.answer(f"⚠️ Different issue detected: {current_issue}", show_alert=True)
        except Exception as e:
            logger.error(f"Rescan failed: {e}")
            await query.answer("❌ Scan failed", show_alert=True)
        return

    # OK/Acknowledge button
    if action == "OK":
        await query.answer("✅ Acknowledged")
        await query.delete_message()
        return

    # SNOOZE button
    if action == "SZ":
        await query.answer()
        pubkey = data[1]
        issue_type = data[2]
        chat_id = str(update.effective_chat.id)
        key = f"{chat_id}_{pubkey}_{issue_type}"

        USER_IGNORES[key] = time.time() + 86400
        db.save_ignores(USER_IGNORES)
        
        await query.edit_message_text(
            f"💤 **Snoozed for 24 Hours**\n\n"
            f"Node: `{pubkey}`\n"
            f"Issue: `{issue_type}`\n\n"
            f"You won't receive alerts about this issue for 24 hours.\n"
            f"Background monitoring continues.\n\n"
            f"⏰ Alerts resume: {datetime.fromtimestamp(USER_IGNORES[key]).strftime('%Y-%m-%d %H:%M')}",
            parse_mode='Markdown'
        )
        return
    
    # IGNORE button
    if action == "IG":
        await query.answer()
        pubkey = data[1]
        issue_type = data[2]
        chat_id = str(update.effective_chat.id)
        key = f"{chat_id}_{pubkey}_{issue_type}"

        USER_IGNORES[key] = time.time() + 31536000  # 1 year = effectively permanent
        db.save_ignores(USER_IGNORES)
        
        await query.edit_message_text(
            f"🔇 **Permanently Ignored**\n\n"
            f"Node: `{pubkey}`\n"
            f"Issue: `{issue_type}`\n\n"
            f"You won't receive alerts about this specific issue anymore.\n\n"
            f"💡 **Note:** Other issues will still trigger alerts.\n"
            f"To re-enable: Remove and re-add the node.",
            parse_mode='Markdown'
        )

# --- 🔬 DIAGNOSTIC FUNCTIONS ---

def diagnose_node(node: dict, max_uptime: float) -> dict:
    """
    Enhanced node diagnosis with detailed analysis.
    Returns comprehensive report with severity classification.
    """
    report = {
        "status": "HEALTHY",
        "diagnosis": "",
        "action": ""
    }
    
    issues = []
    actions = []
    is_critical = False

    # 1. VERSION CHECK (WARNING)
    version = str(node.get('version', ''))
    if '0.8' not in version and '0.9' not in version:
        issues.append("🔸 **Outdated Version** (Not v0.8+)")
        actions.append("• Upgrade to latest stable release (v0.8.x)")
        actions.append("• Check release notes at docs.xandeum.network")

    # 2. UPTIME CHECK (CRITICAL vs WARNING)
    uptime = float(node.get('uptime', 0))
    if uptime < 1800:  # <30 minutes = CRITICAL
        issues.append("🔴 **CRITICAL:** Rapid Restarts (<30 min)")
        actions.append("• Check logs immediately: `docker logs <container>`")
        actions.append("• Verify resource availability (RAM/disk)")
        actions.append("• Review recent configuration changes")
        is_critical = True
    elif uptime < 86400:  # <24 hours = WARNING
        issues.append("🔸 **Low Uptime** (<24 hours)")
        actions.append("• Monitor stability over next few hours")
        actions.append("• Consider using systemd or Docker restart policies")

    # 3. STORAGE CHECK (CRITICAL vs WARNING)
    storage_gb = float(node.get('storage_committed', 0)) / (1024**3)
    if storage_gb < 0.05:  # Essentially zero = CRITICAL
        issues.append("🔴 **CRITICAL:** No Storage Committed")
        actions.append("• Verify storage configuration in config file")
        actions.append("• Ensure storage path is valid and writable")
        actions.append("• Minimum recommended: 100MB (0.1 GB)")
        is_critical = True
    elif storage_gb < 0.1:  # Below target = WARNING
        issues.append("🔸 **Low Storage** (<100 MB)")
        actions.append("• Increase committed storage to ≥100 MB")
        actions.append("• Update storage_committed in configuration")

    # 4. PAGING EFFICIENCY (WARNING only)
    hit_rate = float(node.get('paging_hit_rate', 1.0))
    if hit_rate < 0.85:  # Less than 85% hit rate
        issues.append("🔸 **Low Paging Efficiency** (<85%)")
        actions.append("• Review cache configuration")
        actions.append("• Consider increasing cache size if RAM available")

    # No issues found
    if not issues:
        return report

    # Classify severity
    report['status'] = "CRITICAL" if is_critical else "WARNING"
    report['diagnosis'] = "\n".join(issues)
    report['action'] = "\n".join(actions)

    return report

# --- 🚀 BOT INITIALIZATION ---

async def run_bot():
    """Initialize and run the Telegram bot."""
    if not settings.TELEGRAM_TOKEN:
        logger.warning("⚠️ Telegram Bot Token missing. Bot functionality disabled.")
        return

    try:
        app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
        
        # Register command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("watch", watch_command))
        app.add_handler(CommandHandler("check", check_command))
        app.add_handler(CommandHandler("status", check_command))
        app.add_handler(CommandHandler("list", list_command))
        app.add_handler(CommandHandler("stop", unwatch_command))
        app.add_handler(CommandHandler("unwatch", unwatch_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("stats", stats_command))
        
        # Register callback query handler
        app.add_handler(CallbackQueryHandler(button_handler))

        # Start background watchdog
        if app.job_queue:
            app.job_queue.run_repeating(check_nodes, interval=300, first=10)
            logger.info("✅ Background watchdog scheduled (5 min intervals)")
        
        logger.info("🚀 Sentinel Bot initialization complete")
        
        # Initialize bot
        await app.initialize()
        await app.start()
        
        # Set bot commands menu
        try:
            await app.bot.set_my_commands([
                BotCommand("start", "📊 Dashboard & Status"),
                BotCommand("check", "🔍 Check Node Health"),
                BotCommand("watch", "👁️ Monitor New Node"),
                BotCommand("list", "📋 View Watchlist"),
                BotCommand("stats", "🌐 Network Statistics"),
                BotCommand("stop", "🛑 Stop Monitoring"),
                BotCommand("help", "❓ Command Guide")
            ])
            logger.info("✅ Bot commands menu configured")
        except Exception as e:
            logger.warning(f"Could not set bot commands: {e}")
        
        # Start polling
        await app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Ignore old updates on restart
        )
        
        logger.info("🟢 Sentinel Bot is now ONLINE and accepting commands")
        
    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}", exc_info=True)
        raise

unwatch = unwatch_command
