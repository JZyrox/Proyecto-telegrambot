# Importaciones de librerías necesarias
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from diccionario_api import DictionaryAPI
from config import TOKEN, MAX_DEFINICIONES, MAX_EJEMPLOS
import logging
import asyncio

# Configuración básica de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DiccionarioBot:
    def __init__(self):

        """Inicializa el bot con la aplicación y la API del diccionario"""
        self.app = Application.builder().token(TOKEN).build()
        self.api = DictionaryAPI()
        self._configurar_handlers()

    def _configurar_handlers(self):

        """Configura todos los manejadores de comandos y mensajes"""
        self.app.add_handler(CommandHandler("start", self._inicio))
        self.app.add_handler(CommandHandler("help", self._ayuda))
        self.app.add_handler(CommandHandler("define", self._definir))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._mensaje_texto))
        self.app.add_error_handler(self._manejar_error)

    async def _inicio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        """Envía mensaje de bienvenida con /start"""

        mensaje = (
            "📚 *Diccionario de Inglés*\n\n"
            "Puedo buscar definiciones de palabras en inglés con:\n"
            "- Ejemplos de uso\n"
            "- Pronunciación\n"
            "- Partes gramaticales\n\n"
            "*Cómo usarme:*\n"
            "• Escribe palabras directamente\n"
            "• Usa `/define [palabra]`\n"
            "• Usa `/help` para ayuda\n\n"
            "*Ejemplos:*\n"
            "`/define computer`\n"
        )
        await update.message.reply_text(mensaje, parse_mode='Markdown')

    async def _ayuda(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        """Muestra ayuda con /help"""
        ayuda_msg = (
            "ℹ️ *Ayuda del Diccionario*\n\n"
            "Comandos disponibles:\n"
            "/start - Mensaje de bienvenida\n"
            "/help - Esta ayuda\n"
            "/define [palabra] - Busca una definición\n\n"
            "También puedes escribir palabras directamente"
        )
        await update.message.reply_text(ayuda_msg, parse_mode='Markdown')

    async def _definir(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        """Procesa /define [palabra]"""
        if not context.args:
            await update.message.reply_text("ℹ️ Uso: /define [palabra]")
            return
            
        palabra = " ".join(context.args)
        await self._buscar_definicion(update, palabra)

    async def _mensaje_texto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        """Maneja palabras escritas directamente"""
        palabra = update.message.text.strip()
        await self._buscar_definicion(update, palabra)

    async def _buscar_definicion(self, update: Update, palabra: str):

        """Busca definiciones en la API"""
        try:
            datos_api = await self.api.obtener_definicion(palabra)
            
            if not datos_api:
                await update.message.reply_text(
                    f"🔍 No encontré definición para *{palabra}*\n\n"
                    "Prueba con:\n"
                    "- Ortografía correcta\n"
                    "- Palabras en inglés\n"
                    "- Términos más comunes",
                    parse_mode='Markdown'
                )
                return

            respuesta = self._formatear_respuesta(datos_api[0])
            await update.message.reply_text(respuesta, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("⚠️ Error al procesar tu solicitud")

    def _formatear_respuesta(self, datos: dict) -> str:

        """Formatea la respuesta de la API"""
        palabra = datos.get("word", "")
        significados = datos.get("meanings", [])
        fonetica = datos.get("phonetic", "")
        
        lineas = [f"📚 *{palabra.capitalize()}*"]
        
        if fonetica:
            lineas.append(f"🔊 /{fonetica}/")
        
        for significado in significados[:MAX_DEFINICIONES]:
            parte_gramatical = significado.get("partOfSpeech", "")
            definiciones = significado.get("definitions", [])
            
            lineas.append(f"\n*{parte_gramatical}*")
            
            for i, definicion in enumerate(definiciones[:MAX_DEFINICIONES], 1):
                definicion_texto = definicion.get("definition", "")
                ejemplo = definicion.get("example", "")
                
                lineas.append(f"{i}. {definicion_texto}")
                if ejemplo and i <= MAX_EJEMPLOS:
                    lineas.append(f"   _Ejemplo: {ejemplo}_")
        
        return "\n".join(lineas)

    async def _manejar_error(self, update: object, context: ContextTypes.DEFAULT_TYPE):

        """Maneja errores no capturados"""
        logger.error(f"Error no capturado: {context.error}")
        if isinstance(update, Update) and update.message:
            await update.message.reply_text("⚠️ Ocurrió un error inesperado")

    def run(self):
        
        """Inicia el bot"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.api.conectar())
            logger.info("🤖 Bot iniciado...")
            self.app.run_polling()
        except KeyboardInterrupt:
            logger.info("Deteniendo bot...")
        finally:
            loop.run_until_complete(self.api.cerrar())
            loop.close()

if __name__ == "__main__":
    bot = DiccionarioBot()
    bot.run()