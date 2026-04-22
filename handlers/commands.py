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
        "   *Frecuencias válidas:*\n"
        "   • `5min`, `30min` → minutos\n"
        "   • `1h`, `2h` → horas\n"
        "   • `1:30`, `0:45` → horas:minutos\n"
        "   • `5`, `30` → minutos (por defecto)\n\n"
        "   *Ejemplos:*\n"
        "   `/programar 5min MEDICINA Tomar pastilla`\n"
        "   `/programar 1h REUNION Hora de reunión`\n"
        "   `/programar 1:30 DESCANSO Tiempo de pausa`\n\n"
        "📊 `/estado` - Ver tus recordatorios\n"
        "📊 `/estado [palabra]` - Ver uno específico\n"
        "❌ `/cancelar` - Cancelar todos\n"
        "❌ `/cancelar [palabra]` - Cancelar uno\n"
        "🕐 `/horario` - Horario laboral\n"
        "👥 `/grupo_estado` - Ver todos en el grupo\n"
        "🧹 `/limpiar_grupo` - Cancelar todos (admin)"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de Recordatorios v2.0\n📸 Verificación por fotos\n🔑 Múltiples recordatorios\n⏱️ Frecuencias flexibles")

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