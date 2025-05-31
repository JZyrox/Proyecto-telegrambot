import aiohttp
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class DictionaryAPI:
    def __init__(self):
        self.base_url = "https://api.dictionaryapi.dev/api/v2/entries/en"
        self.session = None

    async def conectar(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))

    async def obtener_definicion(self, palabra: str) -> Optional[List[Dict]]:
        """Obtiene definiciones de la API con manejo robusto de errores"""
        try:
            url = f"{self.base_url}/{palabra.lower()}"
            async with self.session.get(url) as respuesta:
                if respuesta.status == 200:
                    return await respuesta.json()
                logger.warning(f"Palabra no encontrada: {palabra} (código {respuesta.status})")
                return None
        except Exception as e:
            logger.error(f"Error en API: {e}")
            return None

    async def cerrar(self):
        if self.session:
            await self.session.close()