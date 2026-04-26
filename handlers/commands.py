"""Handlers de comandos básicos"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config
from datetime import datetime

logger = setup_logger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome = f"👋 ¡Hola {user.first_name}!\n\n🤖 Bot de recordatorios con verificación por fotos.\n\n📝 Usa /programar para empezar."
    await update.message.reply_text(welcome, reply_markup=inline_keyboards.get_main_menu_keyboard())
    logger.info(f"👤 /start de {user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "*AYUDA DEL BOT*\n\n"
        "*Comandos:*\n\n"
        "📝 `/programar [frecuencia] [palabra] [mensaje]`\n"
        "   Crea un recordatorio que requiere 2 fotos para detenerse\n"
        "   *Frecuencias válidas:*\n"
        "   • `5min`, `30min` → minutos\n"
        "   • `1h`, `2h` → horas\n"
        "   • `1:30`, `0:45` → horas:minutos\n"
        "   • `diario`, `24h` → cada 24 horas\n\n"
        "📝 `/recordar [frecuencia] [palabra]`\n"
        "   Responde a un mensaje y crea un recordatorio simple\n"
        "   El bot reenviará ese mensaje periódicamente\n"
        "   Se detiene solo con `/cancelar [palabra]`\n"
        "   *Ejemplo:* Responde a una foto y escribe `/recordar 24h IMPORTANTE`\n\n"
        "📊 `/estado` - Ver tus recordatorios\n"
        "📊 `/estado [palabra]` - Ver uno específico\n"
        "❌ `/cancelar` - Cancelar todos tus recordatorios\n"
        "❌ `/cancelar [palabra]` - Cancelar uno específico\n"
        "🕐 `/horario` - Ver horario laboral\n"
        "👥 `/grupo_estado` - Ver todos en el grupo\n"
        "🧹 `/limpiar_grupo` - Cancelar todos (admin)"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot de Recordatorios v2.0\n"
        "📸 Verificación por fotos\n"
        "📝 Recordatorios simples\n"
        "⏱️ Frecuencias flexibles"
    )

async def horario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    is_work = Config.is_work_time(now)
    
    if is_work:
        status = "✅ *Estamos en horario laboral*"
    else:
        next_work = Config.get_next_work_time(now)
        status = f"⏸️ *Fuera de horario laboral*\nPróximo inicio: {next_work}"
    
    message = f"{status}\n\n{Config.get_work_schedule_text()}"
    await update.message.reply_text(message, parse_mode='Markdown')

def get_start_handler(): return CommandHandler("start", start_command)
def get_help_handler(): return CommandHandler("help", help_command)
def get_about_handler(): return CommandHandler("about", about_command)
def get_horario_handler(): return CommandHandler("horario", horario_command)